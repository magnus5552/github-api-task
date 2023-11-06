# github-api-task

Асинхронное получение топ пользователей выбранной организации github

## Usage

Создайте файл SECRET_KEY и скопируйте в него ваш апи ключ для github

Получить топ 100 пользователей организации
```shell
python activity_counter.py <organization>
```

Включить логирование запросов в консоли --log
```shell
python activity_counter.py <organization> --log
```