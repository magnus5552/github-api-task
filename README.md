# github-api-task

Асинхронное получение топа пользователей для выбранной организации github

## Usage

Создайте файл SECRET_KEY и скопируйте в него ваш апи ключ для github

Получить топ 100 пользователей организации
```shell
python activity_counter.py <organization>
```

Указать количество пользователей -n
```shell
python activity_counter.py -n N <organization>
```

Включить логирование запросов в консоли --log
```shell
python activity_counter.py --log <organization>
```