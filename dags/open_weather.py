from datetime import datetime,timedelta
import time
import datetime
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import HttpOperator
import json

API ='682dec93d925536760749155cc3096bd'

def kelvin_to_celsius(temp):
    celsius_data=temp-273.15
    return celsius_data

def get_open_weather(task_instance):
    data=task_instance.xcom_pull(task_ids='extract_data')
    name=data["name"]
    description=data["weather"][0]["description"]
    temp=kelvin_to_celsius(data["main"]["temp"])
    feels_like_temp=kelvin_to_celsius(data["main"]["feels_like"])
    pressure=data["main"]["pressure"]
    humidity=data["main"]["humidity"]
    dict_weather_info={
            "Name":name,
            "Description":description,
            "Temp":temp,
            "Feels Like Temp":feels_like_temp,
            "Pressure":pressure,
            "Humidity":humidity
            }
    list_data=[dict_weather_info]
    frame=pd.DataFrame(list_data)

    today=datetime.datetime.now()
    date_str=today.strftime("%d_%m_%Y_%H_%M_%S")
    current_date="current_temp_date_" + date_str
    output=frame.to_csv("C://Users//User//Desktop//Project//{}.csv".format(current_date),index=False)
    return output


default_args={
    'owner':'airflow',
    'depends_on_past':False,
    'start_date':datetime.datetime(2024,4,29),
    'retries':1,
    'retry_delay':datetime.timedelta(minutes=2)
}

with DAG(
    'etl_for_open_weather',
    description='ETL Open Weather',
    default_args=default_args,
    schedule_interval=datetime.timedelta(minutes=2)
) as dag:
    
    open_weather_sensor=HttpSensor(
        task_id='open_weather_sensor',
        http_conn_id='weather_id',
        endpoint='/data/2.5/weather?q=Baku&APPID=682dec93d925536760749155cc3096bd',
        response_check=lambda response:True if response.status_code==200 else False
    )

    extract_data=HttpOperator(
        task_id='extract_data',
        http_conn_id='weather_id',
        method='GET',
        endpoint='/data/2.5/weather?q=Baku&APPID=682dec93d925536760749155cc3096bd',
        response_filter=lambda response:json.loads(response.text),
        log_response=True

    )

    run_etl=PythonOperator(
        task_id='run_etl',
        python_callable=get_open_weather,
        dag=dag
    )

open_weather_sensor>>extract_data>>run_etl