'''
hashing alg:

import hashlib, base64
password = u"pa$$w0rd"

salt= u"change_this_key_please"

bin_password = password.encode('utf-8')
bin_salt = salt.encode('utf-8')

m = hashlib.pbkdf2_hmac('sha256',bin_password,bin_salt,1000)
x = base64.b64encode(m)
print (x)
'''

'''
Privilege bits:
Blog
1. Create / edit / save own posts ("Writer")
2. Edit other's posts, change publishing settings on posts ("Editor"), run publishing actions
4. Edit blog templates ("Designer"), run publishing actions
8. Change blog-wide settings such as categories and other blog user's settings ("Executive editor")
Site:
16. Change sitewide settings, such as the master path, and other site user's settings ("Editor-in-chief")
Ignores blog setting
System:
32. Change systemwide installation settings, such as plugins, and all settings on all sites and blogs ("Administrator")
Ignores site setting


it isn't clear that each setting implies the one below it
so that will have to be set manually when we do the bitwise setting operations
e.g., EIC setting = 16+8+4+2+1
???

Writer: 1
Editor: 1+2
Designer: 4 (note restrictions)
Exec editor: 1+2+4+8
EIC: 1+2+4+8+16
Admin: 1+2+4+8+16+32

ALTERNATE DESIGN - consider implementing
    
1. Create / edit / save own posts ("Contributor")
2. Run publishing queue ("Writer")
4. Edit other's posts, change publishing settings on posts ("Editor")
8. Edit blog templates ("Designer")
16. Change blog-wide settings such as categories and other blog user's settings ("Executive editor")
Site:
32. Change sitewide settings, such as the master path, and other site user's settings ("Editor-in-chief")
Ignores blog setting
System:
64. Change systemwide installation settings, such as plugins, and all settings on all sites and blogs ("Administrator")
Ignores site setting

'''

# plugin = pluginID
    # to associate a schema type with a plugin
    
    # Plugins have an internal ID, and an external name
    # which is derived from the folder name they are installed in
    # this means namespace collisions are all but impossible
    
    # plugin installation is not handled automatically; you MUST run the install routine
    # avoid wasting time with plugin detection on startup
    
    
    # an example for all images on a given blog
    # first, a master object for blogs
    # id = 1
    # object_type = blog
    # object_id = blog.id
    # is_schema = True
    # parent= None (signal that this is a top-level object)
        # id = 2
        # object_type = media
        # object_id = None
        # key = "Image copyright"
        # value = None
        # is_schema = True
        # is_unique = True 
        # value_type = string
        # parent = 1 (this is one of the objects associated with blog 1)
            # id = 3
            # object_type = None
            # object_id = 347
            # key = None
            # value = "(C) 2000 Spumco"
            # is_schema = None
            # is_unique = None [if parent is False, we can set multiple instances]
            # value_type = None 
            # parent = 2 (this is an instance of object type 2)
        # id = 4
        # object_type = media
        # object_id = None
        # Key = "Image alignment"
        # value = none
        # is_schema = True
        # is_unique = True
        # value_type = selector
        # parent = 1
            # id = 5
            # object_type = None
            # object_id = None
            # key = "Left"
            # value = "L"
            # is_schema = True
            # is_unique = None
            # parent = 4
            
            # id = 6
            # object_type = None
            # object_id = None
            # key = "Right"
            # value = "R"
            # is_schema = True
            # is_unique = None
            # parent = 4
            
                # id = 7
                # object_type = media
                # object_id = 347
                # key = "Left" (spurious)
                # value = 6
                # is_schema = None
                # is_unique = None
                # parent = 4

# cascading deletes with this system are difficult to enforce
# also, perhaps the schema for KV and the actual KV should be stored in different places



'''

list view sorting

filter_[num]_has_[field]=value
filter_[num]_not_[field]=value

sort_[num]_[field]_[order]
or just sort_[field]_[order]?

the results can then be bookmarked and returned to


template type = bitwise?

1 = entry template
2 = index template
4 = archive by month
8 = archive by year
16 = archive by author
32 = archive by topic

this makes it easier to compute aggregate archives
e.g., a yearly author archive = 8+16=24
 

how do we handle the way a theme can add settings to a site,
for instance by adding fields to a template?

we might want to have two tables
one for schemas, and another for schema data

schema table has source/parent column
source = what this schema comes from
parent = what this schema is governed by?

schema sources:
- system-level (immutable)
- site
- blog
- media
- page
- theme
    - how to have this then insert stuff that can be recognized elsewhere?
    like a customization for pages?


iterating through valid tags in a template -- easy
1) get everything in {{}}
2) check each one for validity

'''


# TODO: Should we give AUTHOR the right to also include "untrusted" content,
# or make that a separate permission? I'm leaning towards the former

'''
Roles or permissions?

.WRITE_POST
.SUBMIT_UNTRUSTED_CONTENT
.EDIT_POSTS
.VIEW_PUBLISHING_QUEUE
.RUN_PUBLISHING_QUEUE
.VIEW_SYSTEM_LOG
.EDIT_BLOG_TEMPLATES
.EDIT_BLOG_SETTINGS
.EDIT_SITE_SETTINGS
.EDIT_PLUGIN_SETTINGS
.EDIT_SYSTEM_SETTINGS


One drawback to bitwise operators is that we run out of bits.

Might just want to make these explicitly declared boolean columns in the table.

The other advantage to doing it that way is I don't have to fiddle with bits every time
I want to add another granular level of permissions.

Roles would then contain sets of permissions which are applied when the role is used.

'''