import pandas as pd
import tkinter as tk
from tkinter import filedialog
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error

def first_order_model(t, K, T):
    return K * (1 - np.exp(-t / T))

def integrator_model(t, K):
    return K * t

def logistic_model(t, K, a, b):
    return K / (1 + np.exp(-a * (t - b)))

def double_exponential(t, K, A, B, T1, T2):
    return K + A * np.exp(-t / T1) + B * np.exp(-t / T2)

def fit_models(x, y):
    models = [
        {
            "name": "Первый порядок",
            "func": first_order_model,
            "initial": [max(y), 1.0]
        },
        {
            "name": "Интегратор",
            "func": integrator_model,
            "initial": [y[-1] / x[-1]]
        },
        {
            "name": "Логистическая",
            "func": logistic_model,
            "initial": [max(y), 1.0, x[len(x)//2]]
        },
        {
            "name": "Сумма экспонент",
            "func": double_exponential,
            "initial": [max(y), max(y)/2, max(y)/2, 1.0, 0.5]
        }
    ]

    best_result = None

    for model in models:
        try:
            popt, _ = curve_fit(model["func"], x, y, p0=model["initial"], maxfev=10000)
            y_pred = model["func"](x, *popt)
            mse = mean_squared_error(y, y_pred)

            if best_result is None or mse < best_result["mse"]:
                best_result = {
                    "name": model["name"],
                    "func": model["func"],
                    "params": popt,
                    "mse": mse
                }

        except Exception as e:
            print(f"Ошибка для модели {model['name']}: {e}")

    return best_result

def read_excel_to_arrays(file_path):
    try:
        df = pd.read_excel(file_path, header=None)

        if df.shape[1] < 2:
            raise ValueError("В файле должно быть минимум два столбца")

        x = df.iloc[:, 0].to_numpy()
        y = df.iloc[:, 1].to_numpy()

        x_norm = x - x[0]
        y_norm = y - y[0]

        return x_norm, y_norm

    except Exception as e:
        print(f"Ошибка при чтении Excel-файла: {e}")
        return None, None

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Выберите Excel-файл",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    return file_path

if __name__ == "__main__":
    file_path = choose_file()

    if not file_path:
        print("Файл не выбран.")
    else:
        x, y = read_excel_to_arrays(file_path)
        if x is not None and y is not None:
            result = fit_models(x, y)

            if result:
                print(f"\nЛучшая модель: {result['name']}")
                print(f"Параметры: {result['params']}")
                print(f"Среднеквадратичная ошибка: {result['mse']:.6f}")

                if result['name'] == "Первый порядок":
                    K, T = result["params"]
                    print(f"\nФормула: y(t) = {K:.3f} * (1 - exp(-t / {T:.3f}))")
                    print(f"Параметры модели:\n  K = {K:.3f}\n  Временная константа T = {T:.3f} с")

                elif result['name'] == "Интегратор":
                    K, = result["params"]
                    print(f"\nФормула: y(t) = {K:.3f} * t")
                    print(f"Параметр модели:\n  K = {K:.3f} (коэффициент усиления интегратора)")

                elif result['name'] == "Логистическая":
                    K, a, b = result["params"]
                    print(f"\nФормула: y(t) = {K:.3f} / (1 + exp(-{a:.3f} * (t - {b:.3f})))")
                    print(f"Параметры модели:\n  K = {K:.3f}\n  a = {a:.3f} (скорость роста)\n  b = {b:.3f} (сдвиг по времени)")

                elif result['name'] == "Сумма экспонент":
                    K, A, B, T1, T2 = result["params"]
                    print(f"\nФормула: y(t) = {K:.3f} + {A:.3f} * exp(-t / {T1:.3f}) + {B:.3f} * exp(-t / {T2:.3f})")
                    print(f"Параметры модели:")
                    print(f"  K (постоянная составляющая) = {K:.3f}")
                    print(f"  A = {A:.3f}")
                    print(f"  B = {B:.3f}")
                    print(f"  Временная константа T1 = {T1:.3f} с")
                    print(f"  Временная константа T2 = {T2:.3f} с")

            else:
                print("Не удалось подобрать ни одну модель.")

