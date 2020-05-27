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


class OrderContextBindingSpec(pinject.BindingSpec):
    def configure(self, bind):
        bind("order_context", to_class=MemoryOrderContext, in_scope=pinject.PROTOTYPE)


def process_order_no_di():
    order_context = SqlLiteOrderContext()
    order_service = OrderService(order_context)

    order = Order("order-123")
    order_service.process_order(order)


def process_order_di():
    obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
    order_service = obj_graph.provide(OrderService)

    order = Order("order-123")
    order_service.process_order(order)


def process_order_singleton():
    obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
    order_service_1 = obj_graph.provide(OrderService)
    order_service_2 = obj_graph.provide(OrderService)
    print(order_service_1.order_context is order_service_2.order_context)


def process_order_prototype():
    obj_graph = pinject.new_object_graph(binding_specs=[OrderContextBindingSpec()])
    order_service_1 = obj_graph.provide(OrderService)
    order_service_2 = obj_graph.provide(OrderService)
    print(order_service_1.order_context is order_service_2.order_context)


if __name__ == "__main__":
    # process_order_no_di()
    # process_order_di()
    # process_order_singleton()
    process_order_prototype()
