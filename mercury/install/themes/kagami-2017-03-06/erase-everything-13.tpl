% from core.models import Page, Media, Blog, Tag, TagAssociation, Category
% t=Media.delete().where(Media.blog==blog)
% t.execute()
% t=Page.delete().where(Page.blog==blog)
% t.execute()
% TagAssociation.delete().where(TagAssociation.tag << (Tag.select().where(Tag.blog==blog))).execute()
% Tag.delete().where(Tag.blog==blog).execute()
% Category.delete().where(Category.blog==blog).execute()
% Category.clean()
% Media.clean()
% Page.clean()
% Tag.clean()
% from core import cms
% includes_to_insert = blog.ssi_templates
% includes_inserted = cms.build_indexes_fileinfos(includes_to_insert)
% index_objects = cms.build_indexes_fileinfos(blog.index_templates)
Rebuilt {{includes_inserted}} includes and {{index_objects}} index objects.