import settings
def recreate_database():
	
	from models import (db, User, Site, Blog, Page, PageCategory,
		KeyValue, Tag, TagAssociation, Category,
		Theme, Template, TemplateMapping, Media, FileInfo,
		Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log,)	
	
	db.connect()

	with db.atomic():
	
		db.drop_tables((User, Site, Blog, Page, PageCategory,
			KeyValue, Tag, TagAssociation, Category,
			Theme, Template, TemplateMapping, Media, FileInfo,
			Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log),
			safe=True)
		
		db.create_tables((User, Site, Blog, Page, PageCategory,
			KeyValue, Tag, TagAssociation, Category,
			Theme, Template, TemplateMapping, Media, FileInfo,
			Queue, Permission, MediaAssociation, PageRevision, FileInfoContext, Plugin, Log),
			safe=False)
		
		settings.DB.create_index_table()

		db.execute_sql(settings.DB.post_recreate())
	
	db.close()