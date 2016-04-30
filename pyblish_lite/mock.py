import pyblish.api


class MyCollector(pyblish.api.ContextPlugin):
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

    def process(self, instance):
        self.log.info("Validating: %s" % instance)


class MyExtractor(pyblish.api.InstancePlugin):
    order = pyblish.api.ExtractorOrder
    families = ["myFamily"]

    def process(self, instance):
        self.log.info("Extracting: %s" % instance)
