from sklearn.model_selection import KFold
import numpy as np
import os
import shutil
import argparse
import subprocess 
import json

from pathlib import Path
import pathlib

langdata_lstm_Folder = '/home/tesseract_repos/langdata_lstm'
tesstrain_Folder = '/home/tesseract_repos/tesstrain'


groundTruthPath = None
result_folder = None
temp_folder = None

lenguage = None
font_Name = None

#Pasar toda la estructura a Clases y OOP

def extract_compare_Data(archivos_ordenados, test_index, resultFile, modelUsed, recognizeCommand):
    mainLaunchDir = os.getcwd()

    #Nos movemos al directorio donde se encuentra tesseract
    os.chdir(f'{tesstrain_Folder}')

    last = None
    #Launch tesseract recognition from tesseract folder
    #Al haber 3 archivos con el mismo nombre pero distinta extension, nos guardamos el
    #nombre para omitirlo

    for file in test_index:
        file = archivos_ordenados[file]
        
        #Eliminamos el sufijo ".gt" en caso de que exista
        file_ = Path(file)
        nameFile = file_.name.replace(".gt", "")
        nameFile = pathlib.Path(nameFile).stem

        #Capturamos el nombre del fichero en cuestion
        if (last is not None) and (last == nameFile):
            continue
        else:
            print(f'\033[36mRecognizing {nameFile}.\033[0m')
            last = nameFile

        #Reconocer texto
        # textRecognized = subprocess.run([
        #         'tesseract',
        #         f"{groundTruthPath}/{nameFile}.tif",
        #         'stdout',
        #         '--tessdata-dir',  
        #         f'{tesstrain_Folder}/data/{font_Name}_data/{font_Name}-{lenguage}-output',
        #         '--user-words',
        #         f'{langdata_lstm_Folder}/{lenguage}',
        #         '--psm',
        #         '7',
        #         '-l',
        #         f'{font_Name}',
        #         '--loglevel',
        #         'ALL',
        #     ], stdout=subprocess.PIPE)

        textRecognized = recognizeCommand(nameFile)

        #Obtenemos el texto reconocido
        realText = subprocess.run([
                'cat',
                f"{groundTruthPath}/{nameFile}.gt.txt"
            ],stdout=subprocess.PIPE)
        
        #Almacenamos
        file = {}
        file.update({
            "Model": f"{modelUsed}",
            "Real": f"{realText.stdout.decode()}",
            "Reco": f"{textRecognized.stdout.decode()}",
        })

        #Actualizamos hashmap
        resultFile.update({
            f"{nameFile}": file,
        })

    #Volvemos a la carpeta de lanzamiento
    os.chdir(f'{mainLaunchDir}')

def clearModel(lenguage, font_Name):
    subprocess.run([
            'python',
            'trainTess.py',
            '-cl',
            '-l',
            f'{lenguage}',
            '-f',
            f'{font_Name}',
            ])

def modelEvaluation(kf,archivos_ordenados, resultFile, modelName, trainCommand, recognizeCommand):
    percentage = 0.
    steps = 1.0/5.0
    for train_index, test_index in kf.split(archivos_ordenados):
        # if firstTime == False:
        #     firstTime = True
        # else: 
        #     return

        if trainCommand is not None:
            #Mover
            for file in test_index:
                subprocess.run(['mv', '-n',f'{groundTruthPath}/{archivos_ordenados[file]}',  f'{temp_folder}'])

            # archivos = sorted(os.listdir(temp_folder))
            # print(archivos)

            trainCommand()

            # #Devolver a carpeta
            for file in test_index:
                file = archivos_ordenados[file]
                #Devolver a carpeta
                subprocess.run(['mv', '-n',f'{temp_folder}/{file}', f'{groundTruthPath}'])

        #Extraer datos y esribir en archivo de resultados
        extract_compare_Data(archivos_ordenados, test_index, resultFile, modelName,recognizeCommand)

        if trainCommand is not None:
            #Limpiar modelo 
            clearModel(lenguage, font_Name)

        percentage = percentage + steps
        print(f"\033[33mEvaluation:{round((percentage*100),2)}% of 100%\033[0m")

def evaluateModel_A(kf, archivos_ordenados):
    resultFile = {}

    recognitionCommand = lambda nameFile : subprocess.run([
                            'tesseract',
                            f"{groundTruthPath}/{nameFile}.tif",
                            'stdout',
                        ], stdout=subprocess.PIPE)

    modelEvaluation(kf, archivos_ordenados,resultFile,
                     "A: Base tesseract model.",
                     None,
                     recognitionCommand)
    
    #Escribimos en fichero y cerramos
    with open(f"{result_folder}/resultsModel_Default_A.json", "w") as archivo_json:
        json.dump(resultFile, archivo_json, indent = 4)
        
def evaluateModel_B(kf, archivos_ordenados):
    resultFile = {}

    trainCommand =  lambda: subprocess.run([
                            'python',
                            'trainTess.py',
                            '-l',
                            f'{lenguage}',
                            '-f',
                            f'{font_Name}',
                            '-it',
                            '100'
                            ])
    
    recognitionCommand = lambda nameFile : subprocess.run([
                            'tesseract',
                            f"{groundTruthPath}/{nameFile}.tif",
                            'stdout',
                            '--tessdata-dir',  
                            f'{tesstrain_Folder}/data/{font_Name}_data/{font_Name}-{lenguage}-output',
                            '--user-words',
                            f'{langdata_lstm_Folder}/{lenguage}',
                            '--psm',
                            '7',
                            '-l',
                            f'{font_Name}',
                            '--loglevel',
                            'ALL',
                        ], stdout=subprocess.PIPE)
    modelEvaluation(kf, archivos_ordenados, resultFile,
                    f"B: Train a model with a special font: {font_Name}.",
                     trainCommand,
                     recognitionCommand)
    
    #Escribimos en fichero y cerramos
    with open(f"{result_folder}/resultsModel_Font_B.json", "w") as archivo_json:
        json.dump(resultFile, archivo_json, indent = 4)

def evaluateModel_C(kf, archivos_ordenados):
    resultFile = {}

    trainCommand = lambda: subprocess.run([
                            'python',
                            'trainTess.py',
                            '-l',
                            f'{lenguage}',
                            '-f',
                            f'{font_Name}',
                            '-it',
                            '100'
                            ])

    recognitionCommand = lambda nameFile : subprocess.run([
                            'tesseract',
                            f"{groundTruthPath}/{nameFile}.tif",
                            'stdout',
                            '--tessdata-dir',  
                            f'{tesstrain_Folder}/data/{font_Name}_data/{font_Name}-{lenguage}-output',
                            '--user-words',
                            f'{langdata_lstm_Folder}/{lenguage}',
                            '--psm',
                            '7',
                            '-l',
                            f'{font_Name}',
                            '--loglevel',
                            'ALL',
                        ], stdout=subprocess.PIPE)

    modelEvaluation(kf, archivos_ordenados,resultFile,
                    f"C: Train a model with a special font: {font_Name} and text.",
                     trainCommand,
                     recognitionCommand)

    #Escribimos en fichero y cerramos
    with open(f"{result_folder}/resultsModel_Custom_C.json", "w") as archivo_json:
        json.dump(resultFile, archivo_json, indent = 4)

#TODO Para este caso, se usan variables globales para comodidad inmediata, pero se debería 
#realizar sin utilizar variables globales
def evaluate(path, evalAll, A_bool , B_bool , C_bool):
    global groundTruthPath

    groundTruthPath = f'{tesstrain_Folder}/data/{font_Name}_data/{font_Name}-ground-truth/{lenguage}'

    #Limpiamos el ground truth que haya
    subprocess.run([ 'python', 'groundTruth.py', '-cl', '-l',f'{lenguage}','-f',f'{font_Name}'])
    #Creamos el ground truth
    subprocess.run([ 'python', 'groundTruth.py','-l',f'{lenguage}','-f',f'{font_Name}', '-dir' , path])

    # if not os.path.exists(groundTruthPath):
    #     print(f"WARNING: There is no ground-truth folder for font \"{font_Name}\" and \"{lenguage}\".")
    #     print(f"Please make sure you generate a ground-truth for \"{font_Name}\" and \"{lenguage}\".")
    #     return
    
    #Creamos directorio temporal para almacenar los archivos del ground-truth que no se usaran
    mainLaunchDir = os.getcwd()

    global temp_folder
    temp_folder = mainLaunchDir + "/temp"

    global result_folder    
    result_folder = mainLaunchDir + "/resultEvaluation"

    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    if not os.path.exists(result_folder):
        os.mkdir(result_folder)

    #NO SE PUEDE REGENEAR EL GROUNDTRUTH TODO EL RATO PORQUE NO SE PUEDE REALIZAR UN KFOLDING AL PRINCIPIO
    #DAR LA OPCION DE DIRECTORIO ESPECIAL O EL BASE DE TESSERACT

    archivos = os.listdir(groundTruthPath)
    archivos_ordenados = sorted(archivos)
    # print(archivos_ordenados)

    #Generamos particion de 5 grupos para la evaluación.
    kf = KFold(n_splits=5)
    
    #==================================== Entrenamiento y evaluacion
    #Modelos
    #A: Default Tesseract
    if(A_bool or evalAll):
        print("Evaluating model A.")
        evaluateModel_A(kf, archivos_ordenados)
    
    #B: Trained Font overfitted
    if(B_bool or evalAll):
        print("Evaluating model B.")
        # evaluateModel_B(kf, archivos_ordenados)
    
    # C: Trained Font overfitted to custom grount truth test
    
    if(C_bool or evalAll):
        print("Evaluating model C.")
        # evaluateModel_C(kf, archivos_ordenados)
    #=====================================  Eliminamos el directorio temporal
    shutil.rmtree(temp_folder)

def main():
    parser = argparse.ArgumentParser(description='Flags for evaluate models.')
    parser.add_argument('-l','--lenguage', type=str, help='Lenguage name.', default = None)
    parser.add_argument('-f','--fontname', type=str, help='Font name.', default = None)

    #Tres posibles modelos
    parser.add_argument('-A','--A', action='store_true', help='Base tesseract model.')
    parser.add_argument('-B','--B', action='store_true', help='Train a model with a special font.')
    parser.add_argument('-C','--C', action='store_true', help='Train a model with a special font and text.')
    parser.add_argument('-dir','--directory', type=str, help='Directory path with training text.', default = None)

    args = parser.parse_args()
    global lenguage
    if args.lenguage is not None:
        lenguage = args.lenguage
    else:
        print("\033[31mYou must provide at least lenguage to train and evaluate any model.\033[0m")
        print("\033[36mUsage: python evaluateModels.py -l [lenguaje]\033[0m") 
        return
    
    #Si no se especifia alguno, se entrenan todos
    evalAll = not(args.A or args.B or args.C)    

    #Solo se verifica en los modelos B y C, antes de entrenar para lanzar error
    global font_Name
    if args.fontname is not None:
        font_Name = args.fontname
    else:
        print("\033[31mYou must provide at least lenguage and font name to train and evaluate any model.\033[0m")
        print("\033[36mUsage: python evaluateModels.py -l [lenguaje] -f [fontName] -[A/B/C]\033[0m") 
        return
    
    path = f'{langdata_lstm_Folder}/{lenguage}'

    #Ruta personalizada
    if args.directory is not None:
        path = args.directory 

    evaluate(path, evalAll, args.A, args.B, args.C)

    return

if __name__ == "__main__":
    main()