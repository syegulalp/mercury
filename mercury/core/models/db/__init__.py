# read the settings variable
# create the appropriate database class

class InitDBClass():
    def _recreate_database(self):

        module_list = (
            'User', 'Site', 'Blog', 'Page', 'PageCategory', 'KeyValue', 'Tag',
            'TagAssociation', 'Category', 'Theme', 'Template',
            'TemplateRevision', 'TemplateMapping', 'Media', 'FileInfo',
            'Queue', 'Permission', 'MediaAssociation', 'PageRevision',
            'FileInfoContext', 'Plugin', 'Log', 'PluginData', 'ThemeData'
            )

        modules = []

        import importlib
        for n in module_list:
            modules.append(importlib.import_module(n, 'core.models'))

        self.connect()

        with self.atomic():

            self.drop_tables(modules,
                safe=True)

            self.create_tables(modules,
                safe=False)

            self.create_index_table()

            self.execute_sql(self.post_recreate())

        self.close()