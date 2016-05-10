import pyblish.api


class MyAction(pyblish.api.Action):
    label = "My Action"
    on = "processed"

    def process(self, context, plugin):
        self.log.info("Running!")


class MyOtherAction(pyblish.api.Action):
    label = "My Other Action"

    def process(self, context, plugin):
        self.log.info("Running!")


class MyCollector(pyblish.api.ContextPlugin):
    label = "My Collector"
    order = pyblish.api.CollectorOrder

    def process(self, context):
        context.create_instance("MyInstance 1", families=["myFamily"])
        context.create_instance("MyInstance 2", families=["myFamily 2"])
        context.create_instance(
            "MyInstance 3",
            families=["myFamily 2"],
            publish=False
        )


class MyValidator(pyblish.api.InstancePlugin):
    order = pyblish.api.ValidatorOrder
    active = False
    label = "My Validator"
    actions = [MyAction,
               MyOtherAction]

    def process(self, instance):
        self.log.info("Validating: %s" % instance)


class MyExtractor(pyblish.api.InstancePlugin):
    order = pyblish.api.ExtractorOrder
    families = ["myFamily"]
    label = "My Extractor"

    def process(self, instance):
        self.log.info("Extracting: %s" % instance)
