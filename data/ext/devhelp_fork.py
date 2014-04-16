from sphinx.builders.devhelp import DevhelpBuilder


class DevhelpBuilderFork(DevhelpBuilder):
    name = 'devhelpfork'

    def handle_finish(self):
        super(DevhelpBuilderFork, self).handle_finish()
        # we need the inventory for intersphinx
        self.dump_inventory()


def setup(app):
    app.add_builder(DevhelpBuilderFork)
