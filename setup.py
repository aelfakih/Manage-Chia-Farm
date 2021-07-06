from setuptools import setup

setup(
   name='manage-chia-farm',
   version='1.0',
   description='A script that allows chia farmers to manage their farm space, get notified of issues',
   author='Adonis Elfakih',
   author_email='adoniselfakih@gmail.com',
   packages=['manage-chia-farm'],  #same as name
   install_requires=['PyYaml', 'TQDM', 'PyInquirer'], #external packages as dependencies
)