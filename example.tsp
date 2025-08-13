@example({
  street: "123 Main St",
  city: "Anytown",
  country: "USA"
})
model Address {
  street: string;
  city: string;
  country: string;
}

model User {
  name: string;
  age: integer;
  email: string?;
  address: Address;
  tags: string[];
  addresses: Address[];
}

enum Status {
  active,
  inactive,
}

model Company {
  name: string;
  status: Status;
  employees: User[];
}

model WidgetBase {
  @key id: string;
  weight: int32;
  color: "red" | "blue";
}

enum WidgetKind {
  Heavy,
  Light,
}

model HeavyWidget extends WidgetBase {
  kind: WidgetKind.Heavy;
}

model LightWidget extends WidgetBase {
  kind: WidgetKind.Light;
}

@discriminated
union Widget {
  heavy: HeavyWidget,
  light: LightWidget,
}

@error
model Error {
  code: int32;
  message: string;
}

@get op read(@path id: string): Widget | Error;
