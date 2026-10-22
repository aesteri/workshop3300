import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset tasks before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all tasks with default priorities."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_with_valid_priority(client, priority):
    """Create a task with each supported priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Prioritized task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Default a missing creation priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_empty_priority_to_medium(client):
    """Default an empty creation priority to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_legacy_tasks_default_to_medium(client):
    """Return Medium for stored tasks without a priority."""
    response = client.get('/api/tasks')

    assert response.status_code == 200
    data = response.get_json()
    assert data[0]['priority'] == 'Medium'
    assert data[1]['priority'] == 'Medium'


def test_priority_persists_in_get_response(client):
    """Return a created task priority from subsequent GET requests."""
    create_response = client.post(
        '/api/tasks',
        json={"title": "High priority task", "priority": "High"}
    )
    created_task = create_response.get_json()

    get_response = client.get('/api/tasks')
    matching_tasks = [
        task for task in get_response.get_json()
        if task['id'] == created_task['id']
    ]

    assert len(matching_tasks) == 1
    assert matching_tasks[0]['priority'] == 'High'


def test_add_task_rejects_invalid_priority(client):
    """Reject priorities outside the supported values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": "Urgent"}
    )

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid priority'


def test_add_task_success(client):
    """Create a task without changing existing behavior."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject task creation requests without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
