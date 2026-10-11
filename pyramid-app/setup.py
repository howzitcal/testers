from setuptools import find_packages, setup

requires = [
    "pyramid",
    "pyramid_jinja2",
    "pyramid_tm",
    "SQLAlchemy",
    "zope.sqlalchemy",
    "waitress",
    "apscheduler",
    "pastedeploy",
    "plaster_pastedeploy",
]

setup(
    name="leads_app",
    version="0.0.1",
    description="Pyramid lead management POC",
    packages=find_packages(),
    include_package_data=True,
    package_data={"leads_app": ["templates/*.jinja2"]},
    install_requires=requires,
    entry_points={
        "paste.app_factory": [
            "main = leads_app:main",
        ],
    },
)
