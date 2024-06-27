from flask import Flask, render_template, request, jsonify
# from static.find_best_combination import find_the_exact_number

app = Flask(__name__)

from itertools import product
from sympy.utilities.iterables import multiset_permutations
import time
import threading

def perform_operation(num1, num2, op):
    if op == '+':
        return num1 + num2
    elif op == '-':
        if num1 > num2:
            return num1 - num2
    elif op == '*':
        return num1 * num2
    elif op == '/':
        if num2 != 0 and num1 % num2 == 0:
            return num1 // num2
    return None

def apply_operations(nums, ops, target, steps, cache, stop_event):
    if stop_event.is_set():
        return steps, None

    if not nums:
        return steps, None

    state = (tuple(nums), tuple(ops))
    if state in cache:
        return cache[state]

    num1 = nums.pop(0)
    num2 = nums.pop(0)
    op = ops.pop(0)
    result = perform_operation(num1, num2, op)

    if result is None:
        return steps, None

    steps.append(f"{num1} {op} {num2} = {result}")

    if result == target:
        stop_event.set()
        cache[state] = (steps, target)
        return steps, target

    if not nums:
        cache[state] = (steps, result)
        return steps, result

    nums.insert(0, result)
    operations_permutations = list(set(product(ops, repeat=len(nums)-1)))
    number_permutations = list(multiset_permutations(nums))

    closest_steps = list(steps)
    closest_number_reached = result
    min_diff = abs(target - result)

    for perm in number_permutations:
        for ops in operations_permutations:
            steps_copy = list(steps)
            nums_copy = list(perm)
            steps_copy, number_reached = apply_operations(nums_copy, list(ops), target, steps_copy, cache, stop_event)

            if number_reached is None:
                continue
            elif number_reached == target:
                stop_event.set()
                cache[state] = (steps_copy, number_reached)
                return steps_copy, number_reached
            else:
                diff = abs(target - number_reached)
                if diff < min_diff and not stop_event.is_set():
                    min_diff = diff
                    closest_steps = steps_copy
                    closest_number_reached = number_reached

    cache[state] = (closest_steps, closest_number_reached)
    return closest_steps, closest_number_reached

def find_best_combination(nums, target, timeout=30):
    global original_nums
    original_nums = set(nums)

    if target in nums:
        return [f"{target} = {target}"], target, [target], [num for num in nums if num != target]

    operations = ['+', '-', '*', '/']
    closest_steps = None
    closest_number_reached = None
    min_diff = float('inf')

    operations_permutations = list(product(operations, repeat=len(nums)-1))
    number_permutations = list(multiset_permutations(nums))
    cache = {}
    stop_event = threading.Event()
    threads = []

    def thread_task(perm, operations_permutations):
        nonlocal closest_steps, closest_number_reached, min_diff

        for ops in operations_permutations:
            if stop_event.is_set():
                return
            
            steps, number_reached = apply_operations(list(perm), list(ops), target, [], cache, stop_event)
            
            if number_reached is None:
                return
            elif number_reached == target:
                closest_steps, closest_number_reached = steps, number_reached
                return
            else:
                diff = abs(target - number_reached)
                if diff < min_diff and not stop_event.is_set():
                    min_diff = diff
                    closest_steps = steps
                    closest_number_reached = number_reached

    timer = threading.Timer(timeout, stop_event.set)
    timer.start()

    for perm in number_permutations:
        t = threading.Thread(target=thread_task, args=(perm, operations_permutations))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    timer.cancel()

    return closest_steps, closest_number_reached

def find_the_exact_number(nums, target, timeout=30):
    print("\nIntentando conseguir el número", target, "con los números", nums, " en un tiempo máximo de", timeout, "segundos.")

    start_time = time.time()
    steps, number_reached = find_best_combination(nums, target, timeout)
    execution_time = time.time() - start_time

    if number_reached == target:
        print("\nSe ha alcanzado el número objetivo.")
    else:
        print(f"\nNo se ha alcanzado el número objetivo, el número más cercano alcanzado fue {number_reached}, es decir, a {abs(target - number_reached)} del objetivo.")

    if steps:
        while True:
            num_steps = len(steps)
            for i in range(num_steps-1):
                delete_line = True
                last_number = steps[i].split(' ')[-1]

                for j in range(i+1, len(steps)):
                    step_split = steps[j].split(' ')

                    if last_number == step_split[0] or last_number == step_split[2]:
                        delete_line = False
                        break

                if delete_line:
                    steps.pop(i)
                    break

            if num_steps == len(steps):
                break

        used_nums = []

        for step in steps:
            step_split = step.split(' ')
            first_number = int(step_split[0])
            second_number = int(step_split[2])

            if first_number in nums:
                used_nums.append(first_number)
                nums.remove(first_number)
            if second_number in nums:
                used_nums.append(second_number)
                nums.remove(second_number)

        print("\nOperaciones realizadas:")
        for step in steps:
            print("  " + step)
        print("\nNúmeros utilizados:", used_nums)
        print("Números no utilizados:", nums)
        print()

        return steps, used_nums, nums, execution_time

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nums = []
        for i in range(1, 7):
            num = int(request.form[f'number{i}'])
            nums.append(num)

        target = int(request.form['target'])
        timeout = int(request.form['timeout'])

        result, used_nums, not_used_nums, execution_time = find_the_exact_number(nums, target, timeout)

        if result:
            return jsonify({'result': result, 'used_nums': used_nums, 'not_used_nums': not_used_nums, 'execution_time': execution_time})
        else:
            return jsonify({'error': 'No solution found!'})
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
