import tkinter as tk
from tkinter import filedialog

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error


def first_order_model(time_values, gain, time_constant):
    return gain * (1 - np.exp(-time_values / time_constant))


def integrator_model(time_values, gain):
    return gain * time_values


def logistic_model(time_values, gain, slope, midpoint):
    return gain / (1 + np.exp(-slope * (time_values - midpoint)))


def double_exponential_model(time_values, offset, amp_a, amp_b, tau_a, tau_b):
    return offset + amp_a * np.exp(-time_values / tau_a) + amp_b * np.exp(-time_values / tau_b)


def fit_models(time_values, output_values):
    model_candidates = [
        {
            "name": "First-order",
            "func": first_order_model,
            "initial": [max(output_values), 1.0],
        },
        {
            "name": "Integrator",
            "func": integrator_model,
            "initial": [output_values[-1] / time_values[-1]],
        },
        {
            "name": "Logistic",
            "func": logistic_model,
            "initial": [max(output_values), 1.0, time_values[len(time_values) // 2]],
        },
        {
            "name": "Double exponential",
            "func": double_exponential_model,
            "initial": [max(output_values), max(output_values) / 2, max(output_values) / 2, 1.0, 0.5],
        },
    ]

    best_result = None

    for model in model_candidates:
        try:
            optimal_params, _ = curve_fit(
                model["func"],
                time_values,
                output_values,
                p0=model["initial"],
                maxfev=10000,
            )
            predicted_output = model["func"](time_values, *optimal_params)
            mse_value = mean_squared_error(output_values, predicted_output)

            if best_result is None or mse_value < best_result["mse"]:
                best_result = {
                    "name": model["name"],
                    "func": model["func"],
                    "params": optimal_params,
                    "mse": mse_value,
                }

        except Exception as exc:
            print(f"Model fit failed for {model['name']}: {exc}")

    return best_result


def read_excel_to_arrays(file_path):
    try:
        data_frame = pd.read_excel(file_path, header=None)

        if data_frame.shape[1] < 2:
            raise ValueError("Excel file must contain at least two columns.")

        time_values = data_frame.iloc[:, 0].to_numpy()
        output_values = data_frame.iloc[:, 1].to_numpy()

        normalized_time = time_values - time_values[0]
        normalized_output = output_values - output_values[0]

        return normalized_time, normalized_output

    except Exception as exc:
        print(f"Failed to read Excel file: {exc}")
        return None, None


def choose_file():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="Select Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")],
    )


if __name__ == "__main__":
    selected_file = choose_file()

    if not selected_file:
        print("No file selected.")
    else:
        time_values, output_values = read_excel_to_arrays(selected_file)
        if time_values is not None and output_values is not None:
            fit_result = fit_models(time_values, output_values)

            if fit_result:
                print(f"\nBest model: {fit_result['name']}")
                print(f"Parameters: {fit_result['params']}")
                print(f"Mean squared error: {fit_result['mse']:.6f}")

                if fit_result["name"] == "First-order":
                    gain, time_constant = fit_result["params"]
                    print(f"\nFormula: y(t) = {gain:.3f} * (1 - exp(-t / {time_constant:.3f}))")
                    print(f"Gain K = {gain:.3f}")
                    print(f"Time constant T = {time_constant:.3f} s")

                elif fit_result["name"] == "Integrator":
                    (gain,) = fit_result["params"]
                    print(f"\nFormula: y(t) = {gain:.3f} * t")
                    print(f"Gain K = {gain:.3f}")

                elif fit_result["name"] == "Logistic":
                    gain, slope, midpoint = fit_result["params"]
                    print(f"\nFormula: y(t) = {gain:.3f} / (1 + exp(-{slope:.3f} * (t - {midpoint:.3f})))")
                    print(f"Gain K = {gain:.3f}")
                    print(f"Slope a = {slope:.3f}")
                    print(f"Midpoint b = {midpoint:.3f}")

                elif fit_result["name"] == "Double exponential":
                    offset, amp_a, amp_b, tau_a, tau_b = fit_result["params"]
                    print(
                        f"\nFormula: y(t) = {offset:.3f} + {amp_a:.3f} * exp(-t / {tau_a:.3f}) + {amp_b:.3f} * exp(-t / {tau_b:.3f})"
                    )
                    print(f"Offset = {offset:.3f}")
                    print(f"A = {amp_a:.3f}")
                    print(f"B = {amp_b:.3f}")
                    print(f"T1 = {tau_a:.3f} s")
                    print(f"T2 = {tau_b:.3f} s")
            else:
                print("No model could be fitted.")
