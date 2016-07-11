"""Base support and standard choices for conditions."""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from djblets.conditions.errors import (ConditionChoiceConflictError,
                                       ConditionChoiceNotFoundError)
from djblets.registries.registry import (ALREADY_REGISTERED,
                                         ATTRIBUTE_REGISTERED, DEFAULT_ERRORS,
                                         NOT_REGISTERED, OrderedRegistry,
                                         UNREGISTER)


class BaseConditionChoice(object):
    """Base class for a choice for a condition.

    A choice is the primary option in a condition. It generally corresponds to
    an object or attribute that would be matched, and contains a human-readable
    name for the choice, a list of operators that pertain to the choice, and
    the default type of field that a user will be using to select a value.
    """

    #: The ID of the choice.
    #:
    #: This must be unique within a
    #: :py:class:`~djblets.conditions.conditions.ConditionSet`.
    choice_id = None

    #: The displayed name for the choice.
    name = None

    #: The operators for this choice.
    #:
    #: This must be set to an instance of
    #: :py:class:`~djblets.conditions.operators.ConditionOperators`.
    operators = None

    #: The default field type used to prompt and render fields.
    #:
    #: This value will be the default for all operators, unless otherwise
    #: overridden.
    #:
    #: This must be set to an instance of a
    #: :py:class:`~djblets.conditions.values.BaseConditionValueField` subclass.
    default_value_field = None

    def get_operator(self, operator_id):
        """Return an operator instance from this choice with the given ID.

        Instances are not cached. Repeated calls will construct new instances.

        Args:
            operator_id (unicode):
                The ID of the operator to retrieve.

        Returns:
            djblets.conditions.operators.BaseConditionOperator:
            The operator instance matching the ID.

        Raises:
            djblets.conditions.errors.ConditionOperatorNotFoundError:
                No operator was found that matched the given ID.
        """
        return self.operators.get_operator(operator_id, self)

    def get_operators(self):
        """Return a generator for all operator instances for this choice.

        This is a convenience around iterating through all operator classes and
        constructing an instance for each.

        Instances are not cached. Repeated calls will construct new instances.

        Yields:
            djblets.conditions.operators.BaseConditionOperator:
                The operator instance.
        """
        for operator_cls in self.operators:
            yield operator_cls(self)

    def get_match_value(self, value):
        """Return a normalized value used for matching.

        This will take the value provided to the parent
        :py:class:`~djblets.conditions.conditions.Condition` and return either
        that value or some related value.

        It's common for ``value`` to actually be an object, such as a database
        model. In this case, this function may want to return an attribute
        (such as a text attribute) from the object, or an object related to
        this object.

        By default, the value is returned directly.

        Args:
            value (object):
                The value provided to match against.

        Returns:
            object:
            The value that this choice's operators will match against.
        """
        return value


class ConditionChoices(OrderedRegistry):
    """Represents a list of choices for conditions.

    This stores a list of choices that can be used for conditions. It can be
    used in one of two ways:

    1. Created dynamically, taking a list of :py:class:`BaseConditionChoice`
       subclasses as arguments.
    2. Subclassed, with :py:attr:`choice_classes` set to a list of
       :py:class:`BaseConditionChoice` subclasses.

    This works as a :py:ref:`registry <registry-guides>`, allowing additional
    choices to be added dynamically by extensions or other code.
    """

    #: A list of default choices.
    #:
    #: This is only used if a list of choices is not passed to the constructor.
    choice_classes = []

    lookup_attrs = ('choice_id',)
    lookup_error_class = ConditionChoiceNotFoundError
    already_registered_error_class = ConditionChoiceConflictError

    default_errors = dict(DEFAULT_ERRORS, **{
        ALREADY_REGISTERED: _(
            'Could not register condition choice %(item)s: This choice is '
            'already registered or its ID conflicts with another choice.'
        ),
        ATTRIBUTE_REGISTERED: _(
            'Could not register condition choice %(item)s: Another choice '
            '%(duplicate)s) is already registered with the same ID.'
        ),
        NOT_REGISTERED: _(
            'No condition choice was found matching "%(attr_value)s".'
        ),
        UNREGISTER: _(
            'Could not unregister condition choice %(item)s: This condition '
            'was not yet registered.'
        ),
    })

    def __init__(self, choices=[]):
        """Initialize the list of choices.

        Args:
            choices (list of type, optional):
                A list of :py:class:`BaseConditionChoice` subclasses. If this
                is provided, any value set for :py:attr:`choice_classes` will
                be ignored.
        """
        super(ConditionChoices, self).__init__()

        self._choices = choices or self.choice_classes

    def get_choice(self, choice_id):
        """Return a choice instance with the given ID.

        Instances are not cached. Repeated calls will construct new instances.

        Args:
            choice_id (unicode):
                The ID of the choice to retrieve.

        Returns:
            BaseConditionChoice:
            The choice instance matching the ID.

        Raises:
            djblets.conditions.errors.ConditionChoiceNotFoundError:
                No choice was found that matched the given ID.
        """
        choice_cls = self.get('choice_id', choice_id)

        return choice_cls()

    def get_choices(self):
        """Return a generator for all choice instances.

        This is a convenience around iterating through all choice classes and
        constructing an instance for each.

        Instances are not cached. Repeated calls will construct new instances.

        Yields:
            BaseConditionChoice:
            The choice instance.
        """
        for choice_cls in self:
            yield choice_cls()

    def get_defaults(self):
        """Return the default choices for the list.

        This is used internally by the parent registry class, and is based on
        the list of choices provided to the constructor or the value for
        :py:attr:`choice_classes`.

        Returns:
            list of type:
            The default list of choices.
        """
        return self._choices
