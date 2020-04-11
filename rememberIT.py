import tkinter as tk
import tkinter.messagebox
import threading
import os, sys
import json
import copy
import numpy
import time
import math

class MainWindow():
    def __init__(self, parent):
        self.parent = parent

        self.started = False

        self.data = {'__common_priority': 0}  #сумма значений приоритета каждого вопроса (для вычисления вероятности)
        self.dirty = False

        menu = tk.Menu(self.parent)
        self.parent['menu'] = menu

        programmMenu = tk.Menu(menu, tearoff=0)
        programmMenu.add_command(label='Start', command=self.start)
        programmMenu.add_command(label='Stop', command=self.stop)

        editMenu = tk.Menu(menu, tearoff=0)
        editMenu.add_command(label='Add', command=self.addQuestrion)
        editMenu.add_command(label='Delete', command=self.deleteQuestion)
        editMenu.add_command(label='Save', command=self.saveQuestrions)
        editMenu.add_separator()
        editMenu.add_command(label='Clear', command=self.clearQuestrions)

        menu.add_cascade(label='Programm', menu=programmMenu, underline=0)
        menu.add_cascade(label='Edit', menu=editMenu, underline=0)

        self.boxFrame = tk.Frame(self.parent)
        self.boxFrame.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        self.scrollbar = tk.Scrollbar(self.boxFrame, orient=tk.VERTICAL)
        self.listBox = tk.Listbox(self.boxFrame, yscrollcommand=self.scrollbar.set)
        self.scrollbar['command'] = self.listBox.yview
        self.listBox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.buttonsFrame = tk.Frame(self.parent)
        self.buttonsFrame.pack(side=tk.TOP, padx=2, pady=2, fill=tk.X)

        self.intervalLabel = tk.Label(self.buttonsFrame, text='Интервал')
        self.intervalSpinbox = tk.Spinbox(self.buttonsFrame, values=[1, *[x for x in range(5, 31, 5)]])
        self.intervalLabel.pack(side=tk.LEFT)
        self.intervalSpinbox.pack(side=tk.LEFT)

        self.statusbar = self.StatusBar(self.parent, self)
        self.statusbar.pack(side=tk.LEFT)
        self.statusbar.set()
        self.parent.after(5000, self.statusbar.clear)

        self.listBox.bind('<Double-Button-1>', self.chooseQuestion)

        self.load_data()

    def process(self):
        #while True:
        #    for i in range(int(self.intervalSpinbox.get())):
        #        time.sleep(1)

        questions_list = self.data.copy()
        questions_list.pop('__common_priority')
        questions_list = questions_list.keys()
        item = PriorityList({q: self.data[q]['priority'] for q in questions_list}).get(False)
        window = QuestionWindow(self, item, self.data[item])

    def start(self):
        if len(self.data) == 1:
            tk.messagebox.showwarning('Ошибка', 'Пока не добавлено ни одного вопроса.\nНевозможно запустить программу.')
            return

        if not self.started:
            thread = threading.Thread(target=self.process)
            thread.start()


    def stop(self):
        pass

    def addQuestrion(self):
        name = '.'
        while True:
            try:
                self.data[name]
            except:
                break
            else:
                name += '.'
        self.data.update({name: {'variants': {'...': [0, 0]}, 'show_variants': 0, 'priority': 1}})
        self.data['__common_priority'] += 1
        self.statusbar.set_changes()
        self.update_questionList()
        self.listBox.activate(tk.END)
        self.chooseQuestion()
        
    def deleteQuestion(self):
        previous_question = self.data.pop(self.listBox.get(tk.ACTIVE))
        previous_priority = previous_question['priority']
        self.data['__common_priority'] -= previous_priority
        self.statusbar.set_changes()
        self.update_questionList()

    def saveQuestrions(self):
        with open('data.txt', 'w') as fh:
            json.dump(self.data, fh)
        self.statusbar.set()
        self.parent.after(5000, self.statusbar.clear())

    def clearQuestrions(self):
        choice = tk.messagebox.askyesno('Очистить список', 'Вы, действительно, хотите очистить список вопросов?')
        if choice:
            self.data.clear()
            self.statusbar.set_changes()
            self.update_questionList()
            self.data['__common_priority'] = 0

    def chooseQuestion(self, *ignore):
        question_name = self.listBox.get(tk.ACTIVE).strip()
        question_vars = self.data.get(question_name)
        form = EditQuestionWindow(self, question_name, question_vars)


    def load_data(self):
        try:
            with open('data.txt', 'r') as fh:
                self.data = json.load(fh)
        except BaseException as err:
            print(err)
            tk.messagebox.showwarning('Файл не найден', 'Файл с данными не найден')
        self.update_questionList()


    def update_questionList(self):
        self.listBox.delete(0, tk.END)
        for key in self.data.keys():
            if key == '__common_priority':
                continue
            self.listBox.insert(tk.END, key)

    def quit(self, *ignore):
        if self.dirty:
            choice = tk.messagebox.askyesnocancel('Сохранить изменения', 'Сохранить изменения перед выходом?')
            if choice:
                self.saveQuestrions()
            if choice is None:
                return
        self.parent.destroy()


    class StatusBar(tk.Frame):
        def __init__(self, root, parent):
            tk.Frame.__init__(self, root)
            self.parent = parent
            self.statusBar = tk.Label(self, anchor=tk.W)
            self.statusBar.pack(side=tk.LEFT, fill=tk.X)

        def clear(self):
            self.statusBar.config(text='')
            self.statusBar.update_idletasks()

        def set(self, string='Нет изменений'):
            self.statusBar.config(text=string)
            self.statusBar.update_idletasks()
            self.parent.dirty = False

        def set_changes(self, string='Изменения не сохранены'):
            self.statusBar.config(text=string)
            self.statusBar.update_idletasks()
            self.parent.dirty = True

class EditQuestionWindow(tk.Toplevel):
    def __init__(self, parent, name, vars):
        super(EditQuestionWindow, self).__init__()
        self.parent = parent

        self.baseName = name        #Для обращения к исходному словарю в случае изменения вопроса
        self.name = tk.StringVar()
        self.name.set(name)

        self.temp_variants_data = copy.deepcopy(vars)
        self.showVariants = tk.BooleanVar()
        self.showVariants.set(self.temp_variants_data['show_variants'])

        self.temp_varLabel = ''     #Имя выбранного варинта в списке, чтобы оно, в случае изменения именими, являлось ключем к временному словарю с вариантами
        self.varLabel = tk.StringVar()
        self.varShow = tk.BooleanVar()
        self.varCorrect = tk.BooleanVar()


        menu = tk.Menu(self, tearoff=0)
        self['menu'] = menu
        editMenu = tk.Menu(menu, tearoff=0)
        editMenu.add_command(label='Add', command=self.add)
        editMenu.add_command(label='Delete', command=self.delete)
        editMenu.add_separator()
        editMenu.add_command(label='Up Priority', command=self.up_priority)
        menu.add_cascade(label='Options', menu=editMenu, underline=0)

        self.Frame = tk.Frame(self)
        self.Frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.listFrame = tk.Frame(self.Frame)
        self.listFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.questionField = tk.Entry(self.listFrame, textvariable=self.name)
        self.scrollbar = tk.Scrollbar(self.listFrame, orient=tk.VERTICAL)
        self.variantsList = tk.Listbox(self.listFrame, yscrollcommand=self.scrollbar.set)
        self.scrollbar['command'] = self.variantsList.yview

        self.questionField.pack(side=tk.TOP, fill=tk.X)
        self.variantsList.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


        self.editFrame = tk.Frame(self.Frame)
        self.editFrame.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.varLabelEnty = tk.Entry(self.editFrame, textvariable=self.varLabel)
        self.varShowCheckButton = tk.Checkbutton(self.editFrame, variable=self.varShow, text='Показывать вариант')
        self.varCorrectCheckButton = tk.Checkbutton(self.editFrame, variable=self.varCorrect, text='Вариант верный')
        
        self.varLabelEnty.pack(side=tk.TOP)
        self.varShowCheckButton.pack(side=tk.TOP)
        self.varCorrectCheckButton.pack(side=tk.TOP)


        self.optionsFrame = tk.Frame(self)
        self.optionsFrame.pack(side=tk.BOTTOM, fill=tk.X)

        self.showVariantsCheckButton = tk.Checkbutton(self.optionsFrame, variable=self.showVariants, text='Показывать варианты', anchor=tk.W)
        self.okButton = tk.Button(self.optionsFrame, text='ok', command=self.ok)
        self.cancelButton = tk.Button(self.optionsFrame, text='Cancel', command=self.cancel)
        self.showVariantsCheckButton.pack(side=tk.TOP)
        self.cancelButton.pack(side=tk.RIGHT)
        self.okButton.pack(side=tk.RIGHT)
        
        self.update_variantsList()

        self.varLabelEnty.select_to(0)
        self.update_variantsList()
        self.update_editFrame(start=True)

        self.variantsList.bind('<Double-Button-1>', self.update_editFrame)

        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.grab_set()
        self.wait_window(self)

    def add(self):
        self.update_editFrame()
        self.temp_variants_data['variants'].update({'...': [0,0]})
        self.update_variantsList()
        self.variantsList.activate(tk.END)
        self.update_editFrame(start=True)

    def up_priority(self):
        if self.temp_variants_data['priority'] > 1:
            self.temp_variants_data['priority'] -= 1

    def ok(self):
        self.update_editFrame()
        has_changes = self.has_changes()
        if self.save(has_changes):
            self.destroy()

    def cancel(self):
        self.update_editFrame()
        has_changes = self.has_changes()
        if has_changes == [False, True] or has_changes == [True, None]:
            choice = tk.messagebox.askyesnocancel('Сохранить изменения', 'Сохранить изменения?')
            if choice:
                if not self.save(has_changes):
                    return
            if choice is None:
                return
            self.destroy()
        self.destroy()

    def save(self, has_changes: list()):
        if self.name.get() == '__common_priority':
            tk.messagebox.showwarning('Ошибка вопроса', 'Данное название вопроса зарезервировано, невозможно сохранить вопрос.')
            return False

        if has_changes == [True, None]:
            previous_question = self.parent.data.pop(self.baseName)
            previous_question_priority = previous_question['priority']
            delta = previous_question_priority - self.temp_variants_data['priority']
            self.parent.data['__common_priority'] -= delta
            self.parent.data.update({self.name.get(): {'variants': self.temp_variants_data['variants'],
                                                       "show_variants": self.showVariants.get(),
                                                       'priority': self.temp_variants_data['priority']}})
            self.parent.update_questionList()

        if has_changes == [False, True]:
            previous_question_priority = self.parent.data[self.baseName]['priority']
            delta = previous_question_priority - self.temp_variants_data['priority']
            self.parent.data['__common_priority'] -= delta
            self.parent.data[self.baseName] = {'variants': self.temp_variants_data['variants'],
                                               "show_variants": self.showVariants.get(),
                                               'priority': self.temp_variants_data['priority']}
        return True


    def has_changes(self):
        """Есть ли изменения в вопросе
            
           Возвращает кортеж [Изменен ли текст вопроса, Изменен ли вопрос]
                Если изменен текст вопроса, поле i=1 будет None
        """
        question = self.parent.data.get(self.name.get().strip(), False)
        if question:
            if question == self.temp_variants_data:
                return [False, False]
            return [False, True]
        return [True, None]


    def delete(self):
        variantLabel = self.variantsList.get(tk.ACTIVE)
        self.temp_variants_data['variants'].pop(variantLabel)
        self.update_variantsList()
        self.update_editFrame(start=True)
        self.variantsList.activate(tk.END)

    def update_variantsList(self):
        self.variantsList.delete(0, tk.END)
        for var in self.temp_variants_data['variants'].keys():
            self.variantsList.insert(tk.END, var)

    def update_editFrame(self, *ignore, start=False):
        if not start:
            variant = {self.temp_varLabel: self.temp_variants_data['variants'].get(self.temp_varLabel, [])}
            variant_in_field = {self.varLabel.get().strip(): [self.varShow.get(), self.varCorrect.get()]}

            if variant != variant_in_field:
                self.temp_variants_data['variants'].pop(self.temp_varLabel)
                self.temp_variants_data['variants'].update(variant_in_field)
                self.update_variantsList()

            self.temp_variants_data['show_variants'] = self.showVariants.get()

        self.temp_varLabel = self.variantsList.get(tk.ACTIVE).strip()
        self.varLabel.set(self.temp_varLabel)
        self.varShow.set(self.temp_variants_data['variants'][self.temp_varLabel][0])
        self.varCorrect.set(self.temp_variants_data['variants'][self.temp_varLabel][1])

QUESTIONS_EXEC_CODE = """
i=0
while True:
    try:
        var = d.pop()
    except:
        break
    if not var[1][0]:
        continue
    self.vari = tk.BooleanVar()
    self.vars.append(self.vari)
    self.vari.set(0)
    self.variCheckButton = tk.Checkbutton(self.variantsFrame, text=var[0], variable=self.vari)
    self.variCheckButton.pack(side=tk.TOP, fill=tk.X)
    i += 1"""

CHECK_EXEC_CODE="""
for i, var in enumerate(self.vars):     #Проверяем каждый вариант ответа
    variant_label = self.variCheckButton.config()['text'][-1]
    if self.question_data['variants'][variant_label][1] != self.vari.get():
        if self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] != 1:     #В случае, если попытка неверна, увеличиваем приоритет вопроса
            self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] -= 1    
        choice = tk.messagebox.askyesno('Ошибка', 'Неверный ответ на вопрос, попробовать снова?')
        if choice:
            break
        else:
            self.destroy()
else:
    tk.messagebox.showinfo('Отлично', 'Вы правильно ответили на вопрос, поздравляю!')
    self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] += 1     #В случае, если попытка верна, уменьшаем приоритет
    self.destroy()"""



class QuestionWindow(tk.Toplevel):
    def __init__(self, parent, question_label, question_data):
        super(QuestionWindow, self).__init__()
        self.parent = parent
        self.question_data = copy.deepcopy(question_data)

        self.questionLabel = tk.Label(self, text=question_label)
        self.questionLabel.pack(side=tk.TOP, fill=tk.X)

        self.variantsFrame = tk.Frame(self)
        self.variantsFrame.pack(side=tk.TOP, fill=tk.BOTH)

        if self.question_data['show_variants'] == True:
            d = list(question_data['variants'].items())
            self.vars = []
            exec(QUESTIONS_EXEC_CODE)
        else:
            self.var = tk.StringVar()
            self.variantEntry = tk.Entry(self.variantsFrame, textvariable=self.var)
            self.variantEntry.pack()

        self.buttonsFrame = tk.Frame(self)
        self.buttonsFrame.pack(side=tk.BOTTOM, fill=tk.X)

        self.approveButton = tk.Button(self.buttonsFrame, text='Проверить', command=self.check)
        self.approveButton.pack(side=tk.RIGHT)

        self.wm_attributes('-topmost', True)

    def check(self, *ignore):
        if self.question_data['show_variants'] == True:
            exec(CHECK_EXEC_CODE)
        else:
            if not self.question_data['variants'].get(self.var.get().rstrip(), False):
                choice = tk.messagebox.askyesno('Ошибка', 'Неверный ответ на вопрос, попробовать снова?')
        
                if self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] != 1:     #В случае, если попытка неверна, увеличиваем приоритет вопроса
                    self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] -= 1
        
                if choice:
                    return
                else:
                    self.destroy()
            else:
                tk.messagebox.showinfo('Отлично', 'Вы правильно ответили на вопрос, поздравляю!')
                self.parent.data[self.questionLabel.config()['text'][-1]]['priority'] += 1     #В случае, если попытка верна, уменьшаем приоритет
                self.destroy()




class PriorityList():
    def __init__(self, dictionary):
        """dictionary - {'object': priority}
                priority - int(); 1 is the max priority
        """
        max_priority = max(dictionary.values())
        self.__items = list(dictionary.items())
        item_list = [[i[0], max_priority + 1 - int(i[1])] for i in self.__items]
        common_priority = sum([x[1] for x in item_list])
        self.__items = [[i[0], i[1] / common_priority] for i in item_list]

        self.__items = sorted(self.__items, key=lambda x: x[1])
        
        self.__keys, self.__values = [], []
        for item in self.__items:
            self.__keys.append(item[0])
            self.__values.append(item[1])
        self.__values[-1] += (1 - math.fsum(self.__values))

    def get(self, equal_priority=True):
        """random choice of list members, in view of theirs probabilities
        """
        return numpy.random.choice(self.__keys, p=None if equal_priority else self.__values)


app = tk.Tk()
win = MainWindow(app)
app.protocol("WM_DELETE_WINDOW", win.quit)
app.mainloop()

