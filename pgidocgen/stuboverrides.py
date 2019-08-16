
PROPERTY_STUB = """# TODO: Constrain T if possible. Builtins + GTypes might be sufficient?
T = typing.TypeVar('T')

PropertyGetterFn = typing.Callable[[typing.Any], T]
PropertySetterFn = typing.Callable[[typing.Any, T], None]


class Property(typing.Generic[T]):

    name: typing.Optional[str]
    type: typing.Type[T]
    default: typing.Optional[T]
    nick: str
    blurb: str
    flags: ParamFlags
    minimum: typing.Optional[T]
    maximum: typing.Optional[T]

    def __init__(
        self,
        getter: typing.Optional[PropertyGetterFn[T]] = None,
        setter: typing.Optional[PropertySetterFn[T]] = None,
        type: typing.Optional[typing.Type[T]] = None,
        default: typing.Optional[T] = None,
        nick: str = '',
        blurb: str = '',
        flags: ParamFlags = ParamFlags.READWRITE,
        minimum: typing.Optional[T] = None,
        maximum: typing.Optional[T] = None,
    ) -> None:
        ...

    def __get__(self, instance: typing.Any, klass: typing.Type) -> T:
        ...

    def __set__(self, instance: typing.Any, value: T) -> None:
        ...

    def __call__(self, PropertyGetterFn) -> Property[T]:
        ...

    def getter(self: Property[T], fget: PropertyGetterFn) -> Property[T]:
        ...

    def setter(self: Property[T], fset: PropertySetterFn) -> Property[T]:
        ...

    # TODO: There's three Tuple variant structures that could be
    # returned here, and they're all unpleasantly complicated.
    def get_pspec_args(self) -> typing.Sequence[typing.Any]:
        ...
"""

#: Map of namespace to additional manually-written stub classes that
#: should be added to the top of the generated stub.
NAMESPACE_OVERRIDES = {
    'GObject': [
        PROPERTY_STUB,
    ],
}

#: Map of class full name to attributes to be added to the class.
OBJECT_OVERRIDES = {
    'GObject.Object': {
        'Property': 'Property',
    },
}
