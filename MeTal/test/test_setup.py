import unittest
import os

import settings
from core import mgmt

class SetupTest(unittest.TestCase):
    
    
    def setUp(self):

        # tear down and create new DB
        
        from models import init_db
        from core.auth import role
        
        init_db.recreate_database()
        
        new_user = mgmt.create_user(
            name="Administrative User",
            email="admin.user@test-domain.com",
            password="password",            
            )
        
        mgmt.add_user_permission(new_user, 
            permission = role.SYS_ADMIN,
            site = 0)
        
        # create a site
        # create a blog
        # create users for each, assign permissions 
        
    def test_create_admin_user(self):
        print ("hi")
        pass
        
    def test_create_site(self):
        
        pass
    
    def test_create_site_user(self):
        
        pass
    
    def test_create_blog(self):
        
        pass
    
    def test_create_blog_user(self):
        
        pass    

if __name__ == '__main__':
    unittest.main()   
