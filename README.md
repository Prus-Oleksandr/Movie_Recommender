# Movie Recommender project

Django project for recommending movies based on user preferences. 

## Check it out!

https://place_for_render_link

## Installation

Python3 must be already installed

```shell
git clone https://github.com/Prus-Oleksandr/Movie_Recommender
cd Movie_Recommender
python3 -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata data.json
python manage.py runserver # starts Django Server
```

admin:
* username: admin
* password: 1qazcde3

## Features

* Setting preferences based on movie selection among 10 random ones
* Managing preferences(delete favorite directors, genres, actors, add using special search fields, re-register with random films)
* Intuitive minimalist home page with scrolling through recommended movies
* Useful sidebar
* Seamless login via Google account.
* Password reset with email.

## Demo
<img width="3072" height="1728" alt="Вставлене зображення (3)" src="https://github.com/user-attachments/assets/ded12115-a59c-439a-b318-83166fed38fb" />
<img width="3072" height="1728" alt="Вставлене зображення (4)" src="https://github.com/user-attachments/assets/06e59d73-25aa-48d2-af77-9116e8944a24" />
<img width="3072" height="1728" alt="Вставлене зображення (5)" src="https://github.com/user-attachments/assets/a4a9bef8-c10b-4e36-b93b-88b2ed1b6e71" />

