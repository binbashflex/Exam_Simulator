import random
import time
import multiprocessing
import os

F = 1.618

class Students:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender

class Examiners:
    def __init__(self, name):
        self.name = name

class Questions:
    def __init__(self, words):
        self.words = words

def examiner_work(examinator, students_queue, questions, results_queue, stats_queue, status_queue):
    start = time.time()
    lunch_taken = False
    count = 0
    failed = 0

    while not students_queue.empty():
        students_get = students_queue.get()
        count += 1

        status_queue.put(('current', examinator, students_get, time.time() - start))

        save_result, student_time, correct_questions = exam_result(students_get, examinator, questions)

        status_queue.put(('result', examinator, students_get, save_result))

        if save_result == 'Не сдал':
            failed += 1

        results_queue.put((students_get, examinator, save_result, student_time, correct_questions))

        elapsed = time.time() - start

        if elapsed >= 30 and not lunch_taken:
            lunch_time = random.random() * 6 + 12
            time.sleep(lunch_time)
            lunch_taken = True

    work_time = time.time() - start
    stats_queue.put((examinator, count, failed, work_time))

def choose_words_exam(words):
    remaining_words = words.copy()
    select_words = []

    first_words = random.choice(remaining_words)
    select_words.append(first_words)
    remaining_words.remove(first_words)

    while remaining_words and random.random() <= 1/3:
        selected_word = random.choice(remaining_words)
        select_words.append(selected_word)
        remaining_words.remove(selected_word)
    return select_words

def exam_time(examinator):
    name_length = len(examinator.name)
    time_name = random.random() * 2 + (name_length - 1)
    return time_name

def choose_word(words, gender):
    remaining = 1.0
    range_start = 0
    random_num = random.random()

    if gender == 'М':
        last_word = words
    elif gender == 'Ж':
        last_word = words[::-1]

    for word in last_word:
        save_remains = remaining / F
        range_start += save_remains
        remaining = remaining - save_remains
        if random_num <= range_start:
            return  word
    return 'Слово не найдено!'

def exam_result(student, examinator, questions):
    exam_duration = exam_time(examinator)
    result = []
    correct_questions = []
    mood = random.random()
    start = time.time()

    if mood <= 1/8:
        result_exam = 'Не сдал'
    elif mood <= 3/8:
        result_exam = 'Сдал'
    else:
        for i in range(3):
            question = random.choice(questions)

            examiner_result = choose_words_exam(question.words)
            student_words = choose_word(question.words, student.gender)

        if student_words in examiner_result:
            result.append(True)
            correct_questions.append(question)
        else:
            result.append(False)

        correct = result.count(True)
        wrong = result.count(False)

        if correct > wrong:
            result_exam = 'Сдал'
        else:
            result_exam = 'Не сдал'

    elapsed = time.time() - start
    remaining_time = exam_duration - elapsed
    if remaining_time > 0:
        time.sleep(remaining_time)

    elapsed = time.time() - start

    return result_exam, elapsed, correct_questions


def main():
    students = []

    with open('students.txt', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            parts = line.split()

            student = Students(parts[0], parts[1])
            students.append(student)

    examinators = []

    with open('examiners.txt', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            parts = line.split()

            examinator = Examiners(parts[0])
            examinators.append(examinator)

    questions = []

    with open('questions.txt', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            words = line.split()

            question = Questions(words)
            questions.append(question)

    students_queue = multiprocessing.Queue()
    results_queue = multiprocessing.Queue()
    stats_queue = multiprocessing.Queue()
    status_queue = multiprocessing.Queue()

    for student in students:
        students_queue.put(student)

    processes = []

    exam_start = time.time()

    for examinator in examinators:
        process = multiprocessing.Process(
            target=examiner_work,
            args=(examinator, students_queue, questions, results_queue, stats_queue, status_queue)
        )
        process.start()
        processes.append(process)

    student_status = {}

    for student in students:
        student_status[student.name] = 'Очередь'

    current_students = {}

    for examinator in examinators:
        current_students[examinator.name] = '-'

    examiner_stats = {}

    for examinator in examinators:
        examiner_stats[examinator.name] = {
            'count': 0,
            'failed': 0,
            'time': 0
        }

    examiner_start = {}

    for examinator in examinators:
        examiner_start[examinator.name] = None

    while any(process.is_alive() for process in processes):

        if not status_queue.empty():
            message = status_queue.get()

            if message[0] == 'current':
                examinator = message[1]
                student = message[2]

                current_students[examinator.name] = student.name

                if examiner_start[examinator.name] is None:
                    examiner_start[examinator.name] = time.time()

                examiner_stats[examinator.name]['time'] = time.time() - examiner_start[examinator.name]

            elif message[0] == 'result':
                examinator = message[1]
                student = message[2]
                result = message[3]

                current_students[examinator.name] = '-'

                examiner_stats[examinator.name]['count'] += 1

                if result == 'Не сдал':
                    examiner_stats[examinator.name]['failed'] += 1

                if result == 'Сдал':
                    student_status[student.name] = 'Сдал'
                else:
                    student_status[student.name] = 'Провалил'

        os.system('clear')

        status_order = {
            'Очередь': 0,
            'Сдал': 1,
            'Провалил': 2
        }

        print('+------------+----------+')
        print('| Студент    |  Статус  |')
        print('+------------+----------+')

        sorted_students = sorted(
            students,
            key=lambda student: status_order[student_status[student.name]]
        )

        for student in sorted_students:
            print(f'| {student.name:<10} | {student_status[student.name]:^8} |')

        print('+------------+----------+')

        print('+-------------+-----------------+-----------------+---------+--------------+')
        print('| Экзаменатор | Текущий студент | Всего студентов | Завалил | Время работы |')
        print('+-------------+-----------------+-----------------+---------+--------------+')

        for examinator in examinators:
            if examiner_start[examinator.name] is not None:
                examiner_stats[examinator.name]['time'] = time.time() - examiner_start[examinator.name]

        for examinator in examinators:
            stats = examiner_stats[examinator.name]

            print(
                f'| {examinator.name:<11} '
                f'| {current_students[examinator.name]:^15} '
                f'| {stats["count"]:^15} '
                f'| {stats["failed"]:^7} '
                f'| {stats["time"]:^12.2f} |'
            )

        print('+-------------+-----------------+-----------------+---------+--------------+')

        queue_count = 0

        for student in students:
            if student_status[student.name] == 'Очередь':
                queue_count += 1

        print(f'Осталось в очереди: {queue_count} из {len(students)}')

        exam_elapsed = time.time() - exam_start

        print(f'Время с момента начала экзамена: {exam_elapsed:.2f}')

        time.sleep(0.1)

    for process in processes:
        process.join()

    results = []

    for i in students:
        student, examinator, result, student_time, correct_questions = results_queue.get()
        results.append((student, examinator, result, student_time, correct_questions))

    final_order = {
            'Сдал': 0,
            'Провалил': 1
        }

    print('+------------+----------+')
    print('| Студент    |  Статус  |')
    print('+------------+----------+')

    final_students = []

    for student in students:
        for result_student, examinator, result, student_time, correct_questions in results:
            if student.name == result_student.name:

                if result == 'Сдал':
                    status = 'Сдал'
                else:
                    status = 'Провалил'

                final_students.append((student, status))
                break

    final_students.sort(key=lambda item: final_order[item[1]])

    for student, result in final_students:
        print(f'| {student.name:<10} | {result:^8} |')

    print('+------------+----------+')

    stats = []

    for i in examinators:
        examinator, count, failed, work_time = stats_queue.get()
        stats.append((examinator, count, failed, work_time))

    print('+-------------+-----------------+---------+--------------+')
    print('| Экзаменатор | Всего студентов | Завалил | Время работы |')
    print('+-------------+-----------------+---------+--------------+')

    for examinator, count, failed, work_time in stats:
        print(f'| {examinator.name:<11} | {count:^15} | {failed:^7} | {work_time:^12.2f} |')

    print('+-------------+-----------------+---------+--------------+')

    exam_time = time.time() - exam_start
    print(f'Время с момента начала экзамена и до момента и его завершения: {exam_time:.2f}')

    times = []

    for student, examinator, result, student_time, correct_questions in results:
        if result == 'Сдал':
            times.append(student_time)

    best_time = min(times)

    best_students = []

    for student, examinator, result, student_time, correct_questions in results:
        if result == 'Сдал' and student_time == best_time:
            best_students.append(student.name)

    print('Имена лучших студентов:', ', '.join(best_students))

    failed_percent = []

    for examinator, count, failed, work_time in stats:
        if count > 0:
            percent = failed * 100 / count
            failed_percent.append(percent)

    best_percent = min(failed_percent)

    best_examiners = []

    for examinator, count, failed, work_time in stats:
        if count > 0:
            percent = failed * 100 / count

            if percent == best_percent:
                best_examiners.append(examinator.name)

    print('Имена лучших экзаменаторов:', ', '.join(best_examiners))

    failed_times = []

    for student, examinator, result, student_time, correct_questions in results:
        if result == 'Не сдал':
            failed_times.append(student_time)

    best_failed_time = min(failed_times)

    expelled_students = []

    for student, examinator, result, student_time, correct_questions in results:
        if result == 'Не сдал' and student_time == best_failed_time:
            expelled_students.append(student.name)

    print('Имена студентов, которых после экзамена отчислят:', ', '.join(expelled_students))

    question_stats = {}

    for student, examinator, result, student_time, correct_questions in results:
        for question in correct_questions:
            question_name = ' '.join(question.words)
            question_stats[question_name] = question_stats.get(question_name, 0) + 1
            best_count = max(question_stats.values())

    best_questions = []

    for question, count in question_stats.items():
        if count == best_count:
            best_questions.append(question)

    print('Лучшие вопросы:', ', '.join(best_questions))

    result_correct = 0

    for student, examinator, result, student_time, correct_questions in results:
        if result == 'Сдал':
            result_correct += 1

    percent = result_correct * 100 / len(results)

    if percent > 85:
        print('Вывод: Экзамен удался')
    else:
        print('Вывод: Экзамен не удался')

if __name__ == "__main__":
    main()