from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *
from csv import reader
import os
import shutil
from pathlib import Path
import sys

file_name = "3_ft.cae"
model_name = "Model-s16-4"

# file_name = "G:/ABAQUS Einarbeitung/Code/Aktueller_Stand/ft_wib_shear_MA.cae"
# model_name = "Model-s16"

# output folders
output_folders = {".inp": "INP_files", ".cae": "CAE_files", ".jnl": "JNL_files"}

# material selection
material_c = "C30"  # C30 / C35 / C40 / C45
material_s = "S235"  # S235 or S355
material_sas = "SAS_950"  # only option SAS_950

# displacement value
disp = -30.0

# pretension value
P_sas = 1.0 * 841.0  # sigma_sas_max = 841 MPa
P_sas_trans = 1.0 * 841.0  # sigma_sas_trans_max = 841 MPa


# mesh size ratio
alpha = 1.0

# reinforcement ratio for superstructure
beta = 1

# reinforcement radius selection
dia_rf1 = 6.0  # default 6.0  (rf_sas,rf_spz_plate)
dia_rf2 = 7.0  # default 7.0  (rf_sup_trans)
dia_rf3 = 10.0  # default 10.0 (rf_sub_long,...)
dia_rf4 = 10.0  # default 10.0 (rf_sup_long)

# mesh types for volume, beam and rigid elements
mesh_type_volume = C3D8R
mesh_type_beam = B31
mesh_type_rigid = R3D3

# activate wanted mesh controls by removing #
mesh_tech_volume = SWEEP
mesh_algo_volume = MEDIAL_AXIS


# csv paths for material parameters
csv_concrete = (
    "G:/ABAQUS Einarbeitung/Code/Aktueller_Stand/config/concrete_parameters.csv"
)
csv_steel = "G:/ABAQUS Einarbeitung/Code/Aktueller_Stand/config/steel_parameters.csv"


def load_values_from_csv(file_path):
    values = {}

    with open(file_path, "r") as csv_file:
        csv_reader = reader(csv_file, delimiter=";")
        csv_index = next(csv_reader)

        for row in csv_reader:
            current_value = {}

            converted_row = []
            for elem in row:
                try:
                    converted_row.append(float(elem))
                except ValueError:
                    converted_row.append(elem)

            for i, elem in enumerate(converted_row):
                key = csv_index[i]

                if key.endswith("_x"):
                    name = key[:-2]
                    current_value[name] = (elem, converted_row[i + 1])
                elif key.endswith("_y"):
                    continue
                else:
                    current_value[key] = elem

            name = current_value["short_name"]
            values[name] = current_value

    return values


concrete_options = load_values_from_csv(csv_concrete)
steel_options = load_values_from_csv(csv_steel)

rf_pattern = {
    "rf_sup_long_n": beta * 2,
    "rf_sup_long_d": 75.0,
    "rf_sup_trans_n": beta * 8,
    "rf_sup_trans_d": 2.0e03,  # 3_ft -> 2.00e03; 2_ft -> 1.5e03
    "rf_sup_sas_n": 2,
    "rf_sup_sas_d": 60.0,
    "rf_back_n": 2,
    "rf_back_d1": 85.0,
    "rf_back_d2": 160.0,
    "rf_back_d3": 235.0,
    "rf_sub_long_n": 5,
    "rf_sub_long_d": 400.0,
    "rf_sub_trans_n": 5,
    "rf_sub_trans_d": 320.0,
    "rf_sub_sub_trans_n": 5,
    "rf_sub_sub_trans_d": 400.0,
    "rf_sub_sas_n": 4,
    "rf_sub_sas_d": 180.0,
}

linear_patterns = [
    {
        "instanceList": (
            "rf_sup_long-1",
            "rf_sup_long-1-lin-2-1-1",
            "rf_sup_long-1-lin-2-1-2",  # 3_ft
        ),
        "direction1": (-1.0, 0.0, 0.0),
        "number1": rf_pattern["rf_sup_long_n"],
        "spacing1": rf_pattern["rf_sup_long_d"] / (rf_pattern["rf_sup_long_n"] - 1),
    },
    {
        "instanceList": (
            "rf_sup_long-1-lin-5-1",
            "rf_sup_long-1-lin-5-1-lin-2-1",
            "rf_sup_long-1-lin-5-1-lin-2-1-1",  # 3_ft
        ),
        "direction1": (1.0, 0.0, 0.0),
        "number1": rf_pattern["rf_sup_long_n"],
        "spacing1": rf_pattern["rf_sup_long_d"] / (rf_pattern["rf_sup_long_n"] - 1),
    },
    {
        "instanceList": (
            "rf_sup_trans-1-lin-2-1-lin-4-lin-2-1-1",
            "rf_sup_trans-1-lin-4-1-lin-2-lin-2-1",
            "rf_sup_trans-1-lin-4-1-lin-2-lin-2-1-3",  # 3_ft
        ),
        "direction1": (0.0, 0.0, -1.0),
        "number1": rf_pattern["rf_sup_trans_n"],
        "spacing1": rf_pattern["rf_sup_trans_d"] / (rf_pattern["rf_sup_trans_n"] - 1),
        "spacing1": rf_pattern["rf_sup_trans_d"]
        / (rf_pattern["rf_sup_trans_n"]),  # 3_ft
    },
    {
        "instanceList": (
            "rf_sas-2-lin-2-1",
            "rf_sas-2-lin-2-1-lin-2-1",
            "rf_sas-2-lin-2-1-lin-2-1-1",
            "rf_sas-2-lin-2-1-lin-2-1-lin-2-1",
            "rf_sas-2-lin-2-1-lin-2-1-lin-2-1-1",  # 3_ft
            "rf_sas-2-lin-2-1-lin-2-1-lin-lin-2-1",  # 3_ft
        ),
        "direction1": (0.0, -1.0, 0.0),
        "number1": rf_pattern["rf_sup_sas_n"],
        "spacing1": rf_pattern["rf_sup_sas_d"],
    },
    {
        "instanceList": (
            "rf_sub_long-1",
            "rf_sub_long-1-lin-2-1-1",
            "rf_sub_long-1-lin-2-1-2",  # 3_ft
        ),
        "direction1": (-1.0, 0.0, 0.0),
        "number1": rf_pattern["rf_sub_long_n"],
        "spacing1": rf_pattern["rf_sub_long_d"] / (rf_pattern["rf_sub_long_n"] - 1),
    },
    {
        "instanceList": (
            "rf_back-1-lin-1-2-lin-2-1",
            "rf_back-1-lin-1-2",
            "rf_back-1-lin-1-2-lin-2-1-1",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_back_n"],
        "spacing1": rf_pattern["rf_back_d1"],
    },
    {
        "instanceList": (
            "rf_back-1-lin-1-2-lin-2-1",
            "rf_back-1-lin-1-2",
            "rf_back-1-lin-1-2-lin-2-1-1",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_back_n"],
        "spacing1": rf_pattern["rf_back_d2"],
    },
    {
        "instanceList": (
            "rf_back-1-lin-1-2-lin-2-1",
            "rf_back-1-lin-1-2",
            "rf_back-1-lin-1-2-lin-2-1-1",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_back_n"],
        "spacing1": rf_pattern["rf_back_d3"],
    },
    {
        "instanceList": (
            "rf_sub_long-2-1",
            "rf_sub_long-2-1-lin-2-1-1",
            "rf_sub_long-2-1-lin-2-1-2",  # 3_ft
        ),
        "direction1": (-1.0, 0.0, 0.0),
        "number1": rf_pattern["rf_sub_long_n"],
        "spacing1": rf_pattern["rf_sub_long_d"] / (rf_pattern["rf_sub_long_n"] - 1),
    },
    {
        "instanceList": (
            "rf_sub_trans-1",
            "rf_sub_trans-1-lin-2-1-2",
            "rf_sub_trans-1-lin-2-1-3",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_sub_trans_n"],
        "spacing1": rf_pattern["rf_sub_trans_d"]
        / (rf_pattern["rf_sub_sub_trans_n"] - 1),
    },
    {
        "instanceList": (
            "rf_sub_trans-1-lin-2-1-1-lin-1-2",
            "rf_sub_trans-1-lin-2-1-1-lin-lin-2-1",
            "rf_sub_trans-1-lin-2-1-1-lin-lin-2-1-1",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_sub_sub_trans_n"],
        "spacing1": rf_pattern["rf_sub_sub_trans_d"]
        / (rf_pattern["rf_sub_sub_trans_n"] - 1),
    },
    {
        "instanceList": (
            "rf_sas-1-lin-2-1-1",
            "rf_sas-1-lin-1-2-lin-2-1",
            "rf_sas-1-lin-2-1-1-lin-2-1",
            "rf_sas-1-lin-1-2-lin-2-1-lin-2-1",
            "rf_sas-1-lin-2-1-1-lin-2-1-1",  # 3_ft
            "rf_sas-1-lin-1-2-lin-2-1-lin-2-1-1",  # 3_ft
        ),
        "direction1": (0.0, 1.0, 0.0),
        "number1": rf_pattern["rf_sub_sas_n"],
        "spacing1": rf_pattern["rf_sub_sas_d"] / (rf_pattern["rf_sub_long_n"] - 1),
    },
]

value_pretension = {
    "P_sas": P_sas,
    "P_sas_trans": P_sas_trans,
}

reinforcement_radius = {
    "dia_rf1": dia_rf1,
    "dia_rf2": dia_rf2,
    "dia_rf3": dia_rf3,
    "dia_rf4": dia_rf4,
}

mesh_part_rigid = [
    {
        "part_name": "Load_plate",
        "mesh_size": 25.0 * alpha,
        "mesh_type": mesh_type_rigid,
    },
]

mesh_part_beam = [
    {
        "part_name": "rf_back",
        "mesh_size": 42.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_plate_long",
        "mesh_size": 20.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sas",
        "mesh_size": 12.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_spz_plate",
        "mesh_size": 40.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sub_long",
        "mesh_size": 20.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sub_long-2",
        "mesh_size": 20.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sub_trans",
        "mesh_size": 41.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sup_long",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
    {
        "part_name": "rf_sup_trans",
        "mesh_size": 21.0 * alpha,
        "mesh_type": mesh_type_beam,
    },
]

mesh_part_volume = [
    {
        "part_name": "Beam",
        "mesh_size": 15.0 * alpha,
        "mesh_type": mesh_type_volume,
        "mesh_tech": mesh_tech_volume,
        "mesh_algo": mesh_algo_volume,
    },
    {
        "part_name": "Plate_C",
        "mesh_size": 25.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Plate_CF",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Plate_S",
        "mesh_size": 20.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_bot",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_bot-2",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_bot-2-Copy",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_top-l",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_top-r",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "Region_top_ext",
        "mesh_size": 30.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "plate_sas",
        "mesh_size": 10.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "plate_sas-32",
        "mesh_size": 10.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "region_enc",
        "mesh_size": 33.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "sas",
        "mesh_size": 10.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
    {
        "part_name": "sas-trans",
        "mesh_size": 10.0 * alpha,
        "mesh_type": mesh_type_volume,
    },
]

params = {
    "material_c": concrete_options[material_c],
    "material_s": steel_options[material_s],
    "material_sas": steel_options[material_sas],
    "pretension": value_pretension,
    "reinforcement": reinforcement_radius,
    "linear_pattern": linear_patterns,
    "mesh_part_rigid": mesh_part_rigid,
    "mesh_part_beam": mesh_part_beam,
    "mesh_part_volume": mesh_part_volume,
}


def modify_concrete_parameters(material):
    # Unpack dictionary values
    material_name = material["name"]
    E = material["E"]
    Nu = material["Nu"]
    Psi = material["Psi"]
    Ecc = material["Ecc"]
    fb0 = material["fb0/fc0"]
    K = material["K"]
    Visc = material["Visc"]
    C1 = material["C1"]
    C2 = material["C2"]
    C3 = material["C3"]
    C4 = material["C4"]
    C5 = material["C5"]
    C6 = material["C6"]
    C7 = material["C7"]
    C8 = material["C8"]
    C9 = material["C9"]
    C10 = material["C10"]
    C11 = material["C11"]
    C12 = material["C12"]
    C13 = material["C13"]
    C14 = material["C14"]
    C15 = material["C15"]
    C16 = material["C16"]
    C17 = material["C17"]
    C18 = material["C18"]
    C19 = material["C19"]
    C20 = material["C20"]
    C21 = material["C21"]
    C22 = material["C22"]
    C23 = material["C23"]
    C24 = material["C24"]
    C25 = material["C25"]
    C26 = material["C26"]
    C27 = material["C27"]
    C28 = material["C28"]
    C29 = material["C29"]
    C30 = material["C30"]
    C31 = material["C31"]
    C32 = material["C32"]
    C33 = material["C33"]
    C34 = material["C34"]
    C35 = material["C35"]
    C36 = material["C36"]
    C37 = material["C37"]
    C38 = material["C38"]
    C39 = material["C39"]
    C40 = material["C40"]
    C41 = material["C41"]
    C42 = material["C42"]
    C43 = material["C43"]
    C44 = material["C44"]
    C45 = material["C45"]
    C46 = material["C46"]
    C47 = material["C47"]
    C48 = material["C48"]
    C49 = material["C49"]
    C50 = material["C50"]
    C51 = material["C51"]
    C52 = material["C52"]
    C53 = material["C53"]
    C54 = material["C54"]
    C55 = material["C55"]
    C56 = material["C56"]
    C57 = material["C57"]
    C58 = material["C58"]
    T1 = material["T1"]
    T2 = material["T2"]
    T3 = material["T3"]
    T4 = material["T4"]
    T5 = material["T5"]
    T6 = material["T6"]
    T7 = material["T7"]
    T8 = material["T8"]
    T9 = material["T9"]
    T10 = material["T10"]
    T11 = material["T11"]
    T12 = material["T12"]
    T13 = material["T13"]
    T14 = material["T14"]
    T15 = material["T15"]
    T16 = material["T16"]
    T17 = material["T17"]
    T18 = material["T18"]
    CD1 = material["CD1"]
    CD2 = material["CD2"]
    CD3 = material["CD3"]
    CD4 = material["CD4"]
    CD5 = material["CD5"]
    CD6 = material["CD6"]
    CD7 = material["CD7"]
    CD8 = material["CD8"]
    CD9 = material["CD9"]
    CD10 = material["CD10"]
    CD11 = material["CD11"]
    CD12 = material["CD12"]
    CD13 = material["CD13"]
    CD14 = material["CD14"]
    CD15 = material["CD15"]
    CD16 = material["CD16"]
    CD17 = material["CD17"]
    CD18 = material["CD18"]
    CD19 = material["CD19"]
    CD20 = material["CD20"]
    CD21 = material["CD21"]
    CD22 = material["CD22"]
    CD23 = material["CD23"]
    CD24 = material["CD24"]
    CD25 = material["CD25"]
    CD26 = material["CD26"]
    CD27 = material["CD27"]
    CD28 = material["CD28"]
    CD29 = material["CD29"]
    CD30 = material["CD30"]
    CD31 = material["CD31"]
    CD32 = material["CD32"]
    CD33 = material["CD33"]
    CD34 = material["CD34"]
    CD35 = material["CD35"]
    CD36 = material["CD36"]
    CD37 = material["CD37"]
    CD38 = material["CD38"]
    CD39 = material["CD39"]
    CD40 = material["CD40"]
    CD41 = material["CD41"]
    CD42 = material["CD42"]
    CD43 = material["CD43"]
    CD44 = material["CD44"]
    CD45 = material["CD45"]
    CD46 = material["CD46"]
    CD47 = material["CD47"]
    CD48 = material["CD48"]
    CD49 = material["CD49"]
    CD50 = material["CD50"]
    CD51 = material["CD51"]
    CD52 = material["CD52"]
    CD53 = material["CD53"]
    CD54 = material["CD54"]
    CD55 = material["CD55"]
    CD56 = material["CD56"]
    CD57 = material["CD57"]
    CD58 = material["CD58"]
    CD59 = material["CD59"]
    TD1 = material["TD1"]
    TD2 = material["TD2"]
    TD3 = material["TD3"]
    TD4 = material["TD4"]
    TD5 = material["TD5"]
    TD6 = material["TD6"]
    TD7 = material["TD7"]
    TD8 = material["TD8"]
    TD9 = material["TD9"]
    TD10 = material["TD10"]
    TD11 = material["TD11"]
    TD12 = material["TD12"]
    TD13 = material["TD13"]
    # Rho_s           = material["Rho_s"]

    # Access the model database
    model = mdb.models[model_name]

    # Access the material in the model
    material = model.materials["concrete"]

    # Modify the materials values
    material.elastic.setValues(table=((E, Nu),))
    material.concreteDamagedPlasticity.setValues(table=((Psi, Ecc, fb0, K, Visc),))
    material.concreteDamagedPlasticity.concreteCompressionHardening.setValues(
        table=(
            C1,
            C2,
            C3,
            C4,
            C5,
            C6,
            C7,
            C8,
            C9,
            C10,
            C11,
            C12,
            C13,
            C14,
            C15,
            C16,
            C17,
            C18,
            C19,
            C20,
            C21,
            C22,
            C23,
            C24,
            C25,
            C26,
            C27,
            C28,
            C29,
            C30,
            C31,
            C32,
            C33,
            C34,
            C35,
            C36,
            C37,
            C38,
            C39,
            C40,
            C41,
            C42,
            C43,
            C44,
            C45,
            C46,
            C47,
            C48,
            C49,
            C50,
            C51,
            C52,
            C53,
            C54,
            C55,
            C56,
            C57,
            C58,
        )
    )
    material.concreteDamagedPlasticity.concreteTensionStiffening.setValues(
        table=(
            T1,
            T2,
            T3,
            T4,
            T5,
            T6,
            T7,
            T8,
            T9,
            T10,
            T11,
            T12,
            T13,
            T14,
            T15,
            T16,
            T17,
            T18,
        ),
        type=DISPLACEMENT,
    )
    material.concreteDamagedPlasticity.concreteCompressionDamage.setValues(
        table=(
            CD1,
            CD2,
            CD3,
            CD4,
            CD5,
            CD6,
            CD7,
            CD8,
            CD9,
            CD10,
            CD11,
            CD12,
            CD13,
            CD14,
            CD15,
            CD16,
            CD17,
            CD18,
            CD19,
            CD20,
            CD21,
            CD22,
            CD23,
            CD24,
            CD25,
            CD26,
            CD27,
            CD28,
            CD29,
            CD30,
            CD31,
            CD32,
            CD33,
            CD34,
            CD35,
            CD36,
            CD37,
            CD38,
            CD39,
            CD40,
            CD41,
            CD42,
            CD43,
            CD44,
            CD45,
            CD46,
            CD47,
            CD48,
            CD49,
            CD50,
            CD51,
            CD52,
            CD53,
            CD54,
            CD55,
            CD56,
            CD57,
            CD58,
            CD59,
        )
    )
    material.concreteDamagedPlasticity.concreteTensionDamage.setValues(
        table=(
            TD1,
            TD2,
            TD3,
            TD4,
            TD5,
            TD6,
            TD7,
            TD8,
            TD9,
            TD10,
            TD11,
            TD12,
            TD13,
        )
    )
    # Reassign material to section
    model.sections["C"].setValues(material=material_name, thickness=None)
    # Rename the material to selected concrete
    model.materials.changeKey(fromName="concrete", toName=material_name)


def modify_sas_parameters(material):
    # Unpack dictionary values
    material_name = material["name"]
    E = material["E"]
    Nu = material["Nu"]
    Y1 = material["Y1"]
    Y2 = material["Y2"]
    Y3 = material["Y3"]
    Y4 = material["Y4"]

    # Access the model database
    model = mdb.models[model_name]

    # Access the material in the model
    material = model.materials["steel_sas"]

    # Modify the materials values
    material.elastic.setValues(table=((E, Nu),))
    material.plastic.setValues(
        scaleStress=None,
        table=(
            (Y1),
            (Y2),
            (Y3),
            (Y4),
        ),
    )
    # Rename the material to selected sas_steel
    model.materials.changeKey(fromName="steel_sas", toName=material_name)
    # Reassign material steel to sections
    model.sections["sas"].setValues(material=material_name, thickness=None)


def modify_steel_parameters(material):
    # Unpack dictionary values
    material_name = material["name"]
    E = material["E"]
    Nu = material["Nu"]
    Y1 = material["Y1"]
    Y2 = material["Y2"]

    # Access the model database
    model = mdb.models[model_name]

    # Access the material in the model
    material = model.materials["steel"]

    # Modify the materials values
    material.elastic.setValues(table=((E, Nu),))
    material.plastic.setValues(scaleStress=None, table=(Y1, Y2))

    # Rename the material to selected concrete
    model.materials.changeKey(fromName="steel", toName=material_name)
    # Reassign material steel to sections
    model.sections["S"].setValues(material=material_name, thickness=None)


def modify_pretension(value_pretension):
    # Unpack dictionary value
    amount_sas = value_pretension["P_sas"]
    amount_sas_trans = value_pretension["P_sas_trans"]

    # Access the model database
    model = mdb.models[model_name]

    # Modify the amount of pretension force
    a = mdb.models[model_name].rootAssembly
    region = a.sets["set_pretension"]
    mdb.models[model_name].predefinedFields["Predefined Field-sas"].setValues(
        region=region,
        sigma11=0.0,
        sigma22=amount_sas,
        sigma33=0.0,
        sigma12=0.0,
        sigma13=0.0,
        sigma23=0.0,
    )
    region = a.sets["set_pretension_trans"]
    mdb.models[model_name].predefinedFields["Predefined Field-sas_trans"].setValues(
        region=region,
        sigma11=amount_sas_trans,
        sigma22=0.0,
        sigma33=0.0,
        sigma12=0.0,
        sigma13=0.0,
        sigma23=0.0,
    )


def modify_reinforcement_radius(reinforcement_radius):
    # Unpack dictionary value
    dia1 = reinforcement_radius["dia_rf1"]
    dia2 = reinforcement_radius["dia_rf2"]
    dia3 = reinforcement_radius["dia_rf3"]
    dia4 = reinforcement_radius["dia_rf4"]

    # Access the model database
    model = mdb.models[model_name]

    # Modify radius reinforcement sections
    model.profiles["dia1"].setValues(r=dia1)
    model.profiles["dia2"].setValues(r=dia2)
    model.profiles["dia3"].setValues(r=dia3)
    model.profiles["dia4"].setValues(r=dia4)


def modify_reinforcement_linear_pattern(linear_patterns):
    # Access the model database
    a1 = mdb.models[model_name].rootAssembly
    # Access existing "Embedded" Set and convert into list
    orig_edges = a1.sets["embedded"].edges
    all_edges = list(orig_edges)

    for pattern in linear_patterns:
        # Default values because direction2 is not relevant
        number2 = 1
        spacing2 = 1.0
        # Unpack dictionary values
        instanceList = pattern["instanceList"]
        direction1 = pattern["direction1"]
        number1 = pattern["number1"]
        spacing1 = pattern["spacing1"]
        # Generate new reinforment bars
        new_parts = a1.LinearInstancePattern(
            instanceList=instanceList,
            direction1=direction1,
            number1=number1,
            number2=number2,
            spacing1=spacing1,
            spacing2=spacing2,
        )

        # Add newly generated edges from linear pattern to list
        for new_part in new_parts:
            all_edges.extend(new_part.edges)
    # Assign new instances to "Embedded" Set
    a1.Set(edges=part.EdgeArray(all_edges), name="embedded")


def mesh_volume(mesh_part_volume):
    for teile in mesh_part_volume:
        elemname = teile["part_name"]
        elemsize = teile["mesh_size"]
        elemtype = teile["mesh_type"]
        # Select part
        part = mdb.models[model_name].parts[elemname]
        # Delete previous mesh
        part.deleteMesh()
        # Assign new mesh size
        part.seedPart(size=elemsize, deviationFactor=0.1, minSizeFactor=0.1)
        # Assign new mesh type
        elemType1 = mesh.ElemType(
            elemCode=elemtype,
            elemLibrary=STANDARD,
            kinematicSplit=AVERAGE_STRAIN,
            secondOrderAccuracy=OFF,
            hourglassControl=DEFAULT,
            distortionControl=DEFAULT,
        )
        elemType2 = mesh.ElemType(elemCode=C3D6, elemLibrary=STANDARD)
        elemType3 = mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD)
        part = mdb.models[model_name].parts[elemname]
        c = part.cells
        cells = c.getByBoundingBox(
            xMin=-1e10, yMin=-1e10, zMin=-1e10, xMax=1e10, yMax=1e10, zMax=1e10
        )
        pickedRegions = (cells,)
        part.setElementType(
            regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3)
        )
        # Assign new mesh shape
        # part = mdb.models[model_name].parts[elemname]
        # c = part.cells
        # pickedRegions = c.getByBoundingBox(
        #     xMin=-1e10, yMin=-1e10, zMin=-1e10, xMax=1e10, yMax=1e10, zMax=1e10
        # )
        # part.setMeshControls(
        #     regions=pickedRegions, technique=elemtech, algorithm=elemalgo
        # )
        # part = mdb.models[model_name].parts[elemname]
        # Mesh part with selected mesh size and type
        part.generateMesh()


def mesh_rigid(mesh_part_rigid):
    for teile in mesh_part_rigid:
        elemname = teile["part_name"]
        elemsize = teile["mesh_size"]
        elemtype = teile["mesh_type"]
        # Select part
        part = mdb.models[model_name].parts[elemname]
        # Delete previous mesh
        part.deleteMesh()
        # Assign new mesh size
        part.seedPart(size=elemsize, deviationFactor=0.1, minSizeFactor=0.1)
        # Assign new mesh type
        elemType1 = mesh.ElemType(elemCode=elemtype, elemLibrary=STANDARD)
        elemType2 = mesh.ElemType(elemCode=R3D3, elemLibrary=STANDARD)
        part = mdb.models[model_name].parts[elemname]
        f = part.faces
        faces = f.getByBoundingBox(
            xMin=-1e10, yMin=-1e10, zMin=-1e10, xMax=1e10, yMax=1e10, zMax=1e10
        )
        pickedRegions = (faces,)
        part.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2))
        # Mesh part with selected mesh size and type
        part.generateMesh()


def mesh_beam(mesh_part_beam):
    for teile in mesh_part_beam:
        elemname = teile["part_name"]
        elemsize = teile["mesh_size"]
        elemtype = teile["mesh_type"]
        # Select part
        part = mdb.models[model_name].parts[elemname]
        # Delete previous mesh
        part.deleteMesh()
        # Assign new mesh size
        part.seedPart(size=elemsize, deviationFactor=0.1, minSizeFactor=0.1)
        # Assign new mesh type
        elemType1 = mesh.ElemType(elemCode=elemtype, elemLibrary=STANDARD)
        part = mdb.models[model_name].parts[elemname]
        e = part.edges
        edges = e.getByBoundingBox(
            xMin=-1e10, yMin=-1e10, zMin=-1e10, xMax=1e10, yMax=1e10, zMax=1e10
        )
        pickedRegions = (edges,)
        part.setElementType(regions=pickedRegions, elemTypes=(elemType1,))
        # Mesh part with selected mesh size and type
        part.generateMesh()


def apply_load(disp):
    # Access the model database
    model = mdb.models[model_name]
    # edit displacement value
    model.boundaryConditions["BC-load"].setValuesInStep(stepName="Step-2-disp", u2=disp)


executeOnCaeStartup()
openMdb(file_name)

modify_concrete_parameters(params["material_c"])
modify_sas_parameters(params["material_sas"])
modify_steel_parameters(params["material_s"])
modify_pretension(params["pretension"])
modify_reinforcement_radius(params["reinforcement"])
modify_reinforcement_linear_pattern(params["linear_pattern"])
# mesh_rigid(params["mesh_part_rigid"])
mesh_beam(params["mesh_part_beam"])
mesh_volume(params["mesh_part_volume"])
apply_load(disp)

# job name: Automatically generated
job_name = "%s-%s-P_sas%.0f-%.0f-%.0f-%.0f-%.0f-%.0f" % (
    material_c,
    material_s,
    P_sas,
    beta,
    dia_rf1,
    dia_rf2,
    dia_rf3,
    dia_rf4,
)

# Create Job
mdb.Job(
    name=job_name,
    model=model_name,
    description="",
    type=ANALYSIS,
    atTime=None,
    waitMinutes=0,
    waitHours=0,
    queue=None,
    memory=90,
    memoryUnits=PERCENTAGE,
    getMemoryFromAnalysis=True,
    explicitPrecision=SINGLE,
    nodalOutputPrecision=SINGLE,
    echoPrint=OFF,
    modelPrint=OFF,
    contactPrint=OFF,
    historyPrint=OFF,
    userSubroutine="",
    scratch="",
    resultsFormat=ODB,
    numThreadsPerMpiProcess=1,
    multiprocessingMode=DEFAULT,
    numCpus=1,
    numGPUs=0,
)

# Data Check
# mdb.jobs[job_name].submit(consistencyChecking=OFF, datacheckJob=True)

# Write Input
mdb.jobs[job_name].writeInput(consistencyChecking=OFF)

# Save model with selected concrete, steel, pretension values and reinforcement grade and mesh size ratio
mdb.saveAs(job_name + ".cae")

# Close model so files can be moved
mdb.close()


# Get the list of all files in the current folder
current_directory = os.getcwd()
files = os.listdir(current_directory)

print("Moving output files to respective folders")

for file in files:
    # Skip files that have the input file in the name
    ignored_filename = file_name.split(".")[0]
    if ignored_filename in file:
        print("Skipping", file)
        continue

    for ending, folder in output_folders.items():
        if file.endswith(ending):
            new_file = os.path.join(folder, file)
            print("Moving", file, "to", new_file)
            os.replace(file, new_file)
