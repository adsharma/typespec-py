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
