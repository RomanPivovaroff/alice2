from flask import Flask, request, jsonify
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

answer = ''
flag = False
cities = {}
# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return jsonify(response)


def handle_dialog(res, req):
    global flag, answer
    user_id = req['session']['user_id']

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        sessionStorage[user_id]['cities'] = {
            'москва': ['1540737/daa6e420d33102bf6947',
                       '213044/7df73ae4cc715175059e'],
            'нью-йорк': ['1652229/728d5c86707054d4745f',
                         '1030494/aca7ed7acefde2606bdc'],
            'париж': ["1652229/f77136c2364eb90a3ea8",
                      '3450494/aca7ed7acefde22341bdc']
        }
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. отгадаешь город по фото?'
            # получаем варианты buttons из ключей нашего словаря citie
    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    if 'нет' in req['request']['original_utterance']:
        res['response']['end_session'] = True
        res['response']['text'] = 'Прощайте, спасибо за игру!'
        return
    if 'да' in req['request']['original_utterance']:
        if len(sessionStorage[user_id]['cities']) == 0:
            res['response']['end_session'] = True
            res['response']['text'] = 'Прощайте, спасибо за игру!'
            return
        else:
            city = random.choice(list(sessionStorage[user_id]['cities'].keys()))
            while True:
                if len(sessionStorage[user_id]['cities'][city]) == 0:
                    del sessionStorage[user_id]['cities'][city]
                else:
                    break
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'что это за город?'
            res['response']['card']['image_id'] = sessionStorage[user_id]['cities'][city].pop(random.randint(0, 1))
            res['response']['text'] = 'Я угадал!'
            res['response']['buttons'] = [
                {
                    'title': city.title(),
                    'hide': True
                } for city in sessionStorage[user_id]['cities']
            ]
            flag = True
            answer = city
    if flag:
        # ищем город в сообщение от пользователя
        city = get_city(req)
        # если этот город среди известных нам,
        # то показываем его (выбираем одну из двух картинок случайно)
        # если не нашел, то отвечает пользователю
        # 'Первый раз слышу об этом городе.'
        if city in sessionStorage[user_id]['cities']:
            if city == answer:
                res['response']['text'] = 'Правильно! сыграем ещё?'
                flag = False
                del sessionStorage[user_id]['cities'][city]
            else:
                if len(sessionStorage[user_id]['cities'][city]) == 0:
                    flag = False
                    res['response']['text'] = f'вы пытались, это {city}, сыграем ещё?'
                    del sessionStorage[user_id]['cities'][city]
                else:
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['title'] = 'что это за город?'
                    res['response']['card']['image_id'] = sessionStorage[user_id]['cities'][city].pop(0)
                    res['response']['text'] = 'Я угадал!'
                    res['response']['buttons'] = [
                        {
                            'title': city.title(),
                            'hide': True
                        } for city in sessionStorage[user_id]['cities']
                    ]
        else:
            res['response']['text'] = 'назовите город!'



def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()