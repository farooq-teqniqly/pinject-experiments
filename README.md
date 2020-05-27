# Pythonic Dependency Injection with PInject

This article gives a gentle introduction to PInject, a Pythonic dependency injection framework written by Google. 

## Dependency Injection Frameworks
Dependency Injection is a simple concept:
1. Create a graph of object dependencies.
2. When you ask for an object, you get that object with all of its dependencies properly
configured.

A dependency injection framework automates the above steps. A popular dependency framework for Python, and the one we will
use in this article, is [PInject.](https://github.com/google/pinject)

**Note:** Refer to [Wikipedia](https://en.wikipedia.org/wiki/Dependency_injection) if you want to learn more about dependency injection.

## Installing PInject
Install PInject using ```pip```:
```bash
pip install pinject
```

# The Scenario

Let's start with the scenario depicted in the figure below. The diagram shows an order processing service, ```OrderService```
that has a dependency on a ```SqlLiteOrderContext``` which is responsible for persisting orders to a SQLite database.

**class diagram**

Here is the code for the service, context, and ```Order``` class:
```python
class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id

class SqlLiteOrderContext:
    def create_order(self, order: Order):
        print(f"Order created by {self.__class__.__name__}")

class OrderService:
    def __init__(self, sql_lite_order_context: SqlLiteOrderContext):
        self.order_context = sql_lite_order_context

    def process_order(self, order: Order):
        self.order_context.create_order(order)
```

## OrderService Construction Without Dependency Injection

The code below constructs the order service:

```python
    order = Order("order-123")
    context = SqlLiteOrderContext()
    order_service = OrderService(context)
    order_service.process_order(order)
``` 

Run the above code and we get the result:

```bash
Order created by SqlLiteOrderContext
```

There isn't much here to discuss. There is nothing wrong with this code but that
doesn't mean it can't be improved. Introducing a dependency injection framework reduces the amount of code
needed to construct the order service.

## OrderService Construction With Dependency Injection

Now let's have PInject create the order service for us:

```python
import pinject

obj_graph = pinject.new_object_graph()
order_service = obj_graph.provide(OrderService)

order = Order("order-123")
order_service.process_order(order)
```

Running the above code will give the same output as before:
```bash
Order created by SqlLiteOrderContext
```

What did we gain from using PInject? We did not need to instantiate the ```OrderService``` and  ```SqlLiteOrderContext``` instances
ourselves. We simply asked PInject to give us a properly constructed ```OrderService``` instance and that's what it did!

Now consider the case where you have to construct many objects having many dependencies. Constructing that object graph
manually adds a lot of code, is error prone, and brittle. Can you see how PInject makes life easier?

## Deconstructing the Magic
I presume one of the questions you have is how did PInject discover the ```OrderService``` and the ```SqlLiteOrderContext```
objects? This took me a bit of time to grasp because having spent a lot of time in the .NET world I was expecting a requirement 
to [register types with the dependency injector.](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection?view=aspnetcore-3.1#service-registration-methods)

But with PInject all we did was call ```new_object_graph()``` and it discovered ```OrderService``` and the ```SqlLiteOrderContext``` types. How? The answer
is quite simple - PInject discovers types in all loaded modules. 

The next question is how did PInject know to instantiate the ```SqlLiteOrderContext``` type in ```OrderService's``` initializer? One would think
there is some fancy introspection going on but the answer to this question is also simple. Notice the context parameter's name is the
name of the dependent type in snake case. By default, PInject will camel case the parameter name, find the matching class name, and instantiate
that class. With ASP.NET Core dependency injection, parameter names don't matter.

This simple resolution mechanism is called *implicit binding* and is PInject's default behavior. Implicit binding can save
you a lot of work but it isn't suitable for more complex scenarios.

## A More Complex Scenario

You've noticed that unit-testing ```OrderService``` is difficult because of it's dependency on a SQLite database. To address this issue
you decide to create a ```MemoryOrderContext``` type that serves as an in-memory database which makes unit-testing easier. You also
decide to introduce an abstract class, ```OrderContext``` and have the two context classes derive from ```OrderContext.``` Lastly, the
```OrderService``` initializer is changed to accept an abstract ```OrderContext``` instead of a specific implementation.  Here is the updated code:

```python
from abc import ABC, abstractmethod
import pinject

class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id

class OrderContext(ABC):
    @abstractmethod
    def create_order(self, order: Order):
        pass

class SqlLiteOrderContext(OrderContext):
    def create_order(self, order: Order):
        print(f"Order created by {self.__class__.__name__}")

class MemoryOrderContext(OrderContext):
    def create_order(self, order: Order):
        print(f"Order created by {self.__class__.__name__}")

class OrderService:
    def __init__(self, order_context: OrderContext):
        self.order_context = order_context

    def process_order(self, order: Order):
        self.order_context.create_order(order)
```

Run the following code to process an order:

```python
obj_graph = pinject.new_object_graph()
order_service = obj_graph.provide(OrderService)

order = Order("order-123")
order_service.process_order(order)
```

Does it work? No! We get an error about being unable to create an abstract class instance:

```bash
TypeError: Can't instantiate abstract class OrderContext with abstract methods create_order
```

This makes sense because implicit binding, PInject's default behavior, is to camel case the parameter name, ```order_context```,
find a matching class name, ```OrderContext```, and instantiate it which it cannot do because ```OrderContext``` is abstract.

So how do we specify the provider implementation to PInject? We need to be more explicit about our bindings. We do this in PInject through *binding specs.*

## Binding Specs

A binding spec maps parameter names to type names. To get PInject to properly instantiate ```OrderSerivce``` with a particular
context implementation, create a binding spec:

```python
class OrderContextBindingSpec(pinject.BindingSpec):
    def configure(self, bind):
        bind("order_context", to_class=MemoryOrderContext)
``` 

The binding spec associates the ```order_context``` parameter name in the ```OrderService``` initializer with the ```MemoryOrderContext``` type. Now
PInject will instantiate ```MemoryOrderContext``` as an ```OrderService``` dependency.

Modify the driver code by telling PInject about the binding spec:

```python
obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
order_service = obj_graph.provide(OrderService)

order = Order("order-123")
order_service.process_order(order)
```

Run the above code and *voila*, PInject creates the right context!

```bash
Order created by MemoryOrderContext
```

If you're used to .NET Core dependency injection, the binding spec might remind you of the registration methods that
must be called with .NET Core. Therefore the major difference with PInject is its implicit binding mode which .NET Core dependency
injection does not offer.

## Scopes
Scopes are an important concept to understand when using dependency injection frameworks. The scope controls whether the objects
you get from the  dependency injector is a singleton or a new object. With PInject, the object injected through a function parameter is always a singleton. That means
you get the *same* object back. So if you ask for ```OrderService``` in Module A and then ask for it in Module B, you get the
same context instance back. The following code makes this clear:

```python
obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
order_service_1 = obj_graph.provide(OrderService)
order_service_2 = obj_graph.provide(OrderService)
print(order_service_1.order_context is order_service_2.order_context)
```

The ```print()``` statement outputs ```True``` proving that the ```MemoryOrderContext``` is being reused.

What if you want a new instance of ```MemoryOrderContext``` returned each time? PInject offers a scope named ```PROTOTYPE.```
For this to work, add the ```in_scope``` parameter to the call to ```bind()``` in the binding spec's ```configure()``` function:

```python
bind("order_context", to_class=MemoryOrderContext, in_scope=pinject.PROTOTYPE)
```

Re-run the test code:
```python
obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
order_service_1 = obj_graph.provide(OrderService)
order_service_2 = obj_graph.provide(OrderService)
print(order_service_1.order_context is order_service_2.order_context)
```
This time the output is ```False``` meaning that the order services have different contexts.

## Conclusion

Dependency injection frameworks are useful even in a dynamically typed language like Python. I hope you found this introduction
useful and give PInject a try. Thanks for reading!