# Global imports
from copy import copy

# Enthought library imports
from enthought.traits.api import Str, Instance, Dict, on_trait_change, Bool
from enthought.blocks.api import Block
from enthought.contexts.data_context import DataContext
from enthought.contexts.items_modified_event import ItemsModified
from enthought.contexts.data_context import ListenableMixin


class FormulaExecutingContext(DataContext):
    """A class that manages execution between a code block, and spreadsheet like
    expressions that can be assigned to variables"""

    # The underlying context
    data_context = Instance(ListenableMixin)

    # The block that is generated by the expressions in the context
    external_code = Str("pass\n")

    # The user-supplied block that is merged with the expressions
    external_block = Instance(Block)

    # Whether data has changed so as to need execution -- we may want
    # to store up a list of variables that have changed to aid this.
    execution_needed = Bool(False)

    # Whether to automatically re-execute when a variable changes
    auto_execute = Bool(True)

    # Whether to continue on exceptions from execution
    continue_on_errors = Bool(True)

    # Whether to swallow exceptions from the block
    swallow_exceptions = Bool(False)

    # A block representing the external block plus all of the expressions
    _composite_block = Instance(Block)
    # A block representing just the expressions
    _expression_block = Instance(Block)
    # The expressions to execute
    _expressions = Dict

    _globals_context = Instance(DataContext) # May want to change to an interface spec
    # Whether we are currently executing on the DataContext
    _executing = Bool(False)

    # Dict interface
    def __setitem__(self, key, value):
        # FIXME this heuristic of looking for an = is somewhat brittle, but will work for our application
        if isinstance(value, basestring) and '=' in value:
            #This is a formula
            self._expressions[key] = value.split('=')[1]
            self._regenerate_expression_block()
            self._regenerate_composite_block()
            self.execute_block(outputs=[key])
        # FIXME we should be caching these restrictions
        else:
            self.data_context[key] = value

    def __getitem__(self, key):
        try:
            if key in self._expressions:
                return repr(self.data_context[key]) + '=' + self._expressions[key]
            else:
                return self.data_context[key]
        except:
            import pdb; pdb.set_trace()

    def keys(self):
        return self.data_context.keys()
    # FIXME implement __delitem__

    # Public interface

    def __init__(self, **kwtraits):
        if 'external_block' in kwtraits:
            self.external_block = kwtraits.pop('external_block')

        super(FormulaExecutingContext, self).__init__(**kwtraits)
        self._regenerate_expression_block()

        if self.external_block is None:
            self._external_code_changed(self.external_code)
        else:
            self.external_block = Block([self.external_block, Block(self.external_code)])

        self._regenerate_composite_block()


    def execute_block_if_auto(self, inputs=(), outputs=()):
        if self.auto_execute:
            self.execute_block(inputs=inputs, outputs=outputs)
        else:
            self.execution_needed = True
        return

    def execute_if_needed(self):
        if self.execution_needed:
            self.execute_block()
        return

    def execute_block(self, inputs=(), outputs=()):
        if self.data_context is None:
            return

        self._executing = True
        self.data_context.defer_events=True

        if self._composite_block is None:
            self._regenerate_composite_block()
        if inputs !=() or outputs != ():
            block = self._composite_block.restrict(inputs=inputs, outputs=outputs)
        else:
            block = self._composite_block

        old_defer_events = self.data_context.defer_events


        if self.swallow_exceptions:
            try:
                self.data_context.defer_events = True
                block.execute(self.data_context, self._globals_context,
                              continue_on_errors=self.continue_on_errors)
                self.data_context.defer_events = old_defer_events
            except:
                self.data_context.defer_events = old_defer_events

        else:
            try:
                self.data_context.defer_events = True
                block.execute(self.data_context, self._globals_context,
                              continue_on_errors=self.continue_on_errors)
                self.data_context.defer_events = old_defer_events
            except Exception, ex:
                self.data_context.defer_events = old_defer_events
                raise ex

        self._executing = False
        self.data_context.defer_events=False

        execution_needed=False
        return

    def copy(self):
        """Make a deep copy of this FormulaExecutingContext.  Useful for plot shadowing."""
        new_datacontext = DataContext()
        for key in self.data_context.keys():
            try:
                new_datacontext[key] = copy(self.data_context[key])
            except:
                new_datacontext[key] = self.data_context[key]

        # turn off auto-firing of events during construction, then turn it back on
        # after everything is set up

        new = FormulaExecutingContext(data_context=new_datacontext,
                                      external_block=self.external_block,
                                      execution_needed=self.execution_needed,
                                      auto_execute=False,
                                      _expressions=self._expressions)

        new._regenerate_expression_block()
        new._regenerate_composite_block()

        new.auto_execute = self.auto_execute

        return new




    # Trait listeners
    def _data_context_changed(self):
        self.execution_needed=True

    def _external_code_changed(self, new):
        self.external_block = Block(new)
        return


    def _external_block_changed(self, new):
        self._regenerate_composite_block()
        self.execute_block_if_auto()

    def _expression_block_changed(self, new):
        self._regenerate_composite_block()
        self.execute_block_if_auto()

    def _regenerate_composite_block(self):
        self._composite_block = Block((self.external_block, self._expression_block))
        return

    def _regenerate_expression_block(self):
        exprs = ['%s = %s' % (var, expr) for var, expr in self._expressions.items()]
        expression_code = '\n'.join(exprs) + '\n'
        self._expression_block = Block(expression_code)

    @on_trait_change('data_context:items_modified')
    def _data_context_items_modified(self, event):
        if not self._executing and isinstance(event, ItemsModified):
            inputs=set(self._composite_block.inputs).intersection(set(event.added + event.removed + event.modified))
            if len(inputs) == 0:
                return
            self.execute_block_if_auto(inputs=inputs)
        return

    def __composite_block_default(self):
        return Block('')

    def __expression_block_default(self):
        return Block('')



