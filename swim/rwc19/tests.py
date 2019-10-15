from django.test import TestCase
from rwc19.models import Profile
from django.contrib.auth.models import User

# Create your tests here.

def create_profiles():
    user_jim = User.objects.create(username = 'jim', email = 'jim@west.net.nz', password = 'jimpassword')
    user_jim.save()
    user_john = User.objects.create(username = 'john', email = 'john@west.net.nz', password = 'johnpassword')
    user_john.save()
    user_jane = User.objects.create(username = 'jane', email = 'jane@west.net.nz', password = 'janepassword')
    user_jane.save()

class ProfileModelTests(TestCase):
    def test_positive_total_points(self):
        create_profiles()
        user_jim = User.objects.get(username='jim')
        profile_jim = Profile(user=user_jim)
        self.assertIs(profile_jim.totalPoints >= 0, True )