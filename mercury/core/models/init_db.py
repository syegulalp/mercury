import settings
def recreate_database():

	from core.models import (db, User, Site, Blog, Page, PageCategory,
		KeyValue, Tag, TagAssociation, Category,
		Theme, Template, TemplateRevision, TemplateMapping, Media, FileInfo,
		Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log, PluginData,
		ThemeData)

	db.connect()

	with db.atomic():

		db.drop_tables((User, Site, Blog, Page, PageCategory,
			KeyValue, Tag, TagAssociation, Category,
			Theme, Template, TemplateRevision, TemplateMapping, Media, FileInfo,
			Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log, PluginData,
			ThemeData),
			safe=True)

		db.create_tables((User, Site, Blog, Page, PageCategory,
			KeyValue, Tag, TagAssociation, Category,
			Theme, Template, TemplateRevision, TemplateMapping, Media, FileInfo,
			Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log, PluginData,
			ThemeData),
			safe=False)

		settings.DB.create_index_table()

		db.execute_sql(settings.DB.post_recreate())

	db.close()
