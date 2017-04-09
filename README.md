# Adams App

## Installing required packages
You can install all packages required for the project using

```pip install -r dependencies.txt```

To capture the dependencies used by a project by using pip freeze. Make sure the virtual environment is set up to only capture dependencies relevant to the project.
```pip freeze > dependencies.txt```


## Running the web app
Navigate to the directory that contains ```manage.py``` (this should be  ```cd ./adamsapp```) and run the applications using

```python manage.py runserver```

Navigate to http://localhost:8000/ to view the web app.
