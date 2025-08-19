import requests

from pycsghub.utils import (build_csg_headers,
                            get_endpoint)


def list(
        user_name: str,
        token: str,
        endpoint: str,
        limit: int,
):
    action_endpoint = get_endpoint(endpoint=endpoint)
    url = f"{action_endpoint}/api/v1/user/{user_name}/finetune/instances"
    data = {
        "per": limit,
    }
    headers = build_csg_headers(token=token, headers={
        "Content-Type": "application/json"
    })
    response = requests.get(url, params=data, headers=headers)
    response.raise_for_status()
    instances = response.json()['data']
    print(f"{'ID':<10}{'Name':<40}{'Model':<50}{'Status':<10}")
    print("-" * 110)
    if instances:
        for instance in instances:
            print(f"{instance['deploy_id']:<10}"
                  f"{instance['deploy_name']:<40}"
                  f"{instance['model_id']:<50}"
                  f"{instance['status']:<10}")


def start(
        id: int,
        model: str,
        token: str,
        endpoint: str,
):
    action_endpoint = get_endpoint(endpoint=endpoint)
    url = f"{action_endpoint}/api/v1/models/{model}/finetune/{id}/start"
    headers = build_csg_headers(token=token, headers={
        "Content-Type": "application/json"
    })
    response = requests.put(url, headers=headers)
    result = response.json()
    print(result)


def stop(
        id: int,
        model: str,
        token: str,
        endpoint: str,
):
    action_endpoint = get_endpoint(endpoint=endpoint)
    url = f"{action_endpoint}/api/v1/models/{model}/finetune/{id}/stop"
    headers = build_csg_headers(token=token, headers={
        "Content-Type": "application/json"
    })
    response = requests.put(url, headers=headers)
    result = response.json()
    print(result)
