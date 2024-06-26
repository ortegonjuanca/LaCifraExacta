from flask import Flask, render_template, request, jsonify
from static.find_best_combination import find_the_exact_number

app = Flask(__name__)

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
    app.run()
