"""Tests on the Charlotte CLI."""

import pytest
from src.cli import (
    create_db, create_user, drop_tables, rotate_user_key
)
from src.auth import validate_api_key
from src.model import db

def test_database_creation(app, runner):
    """Tests the ability to create table structure from the CLI.
    """
    result = runner.invoke(create_db)
    assert not result.exception
    assert 'Creating table structure...' in result.output
    assert 'Tables have been created.' in result.output

    # Were our tables actually created?
    with app.app_context():
        assert db.engine.has_table('user')
        assert db.engine.has_table('link')


def test_user_creation(app, runner):
    """Tests the ability to generate an API key from the CLI.
    """
    result = runner.invoke(create_user, input="TestMatt\n")
    assert not result.exception
    output_lines = result.output.split('\n')

    assert output_lines[2] == 'Created new user! Below are the user details:'
    output_name = output_lines[3].split(' ')[1]  # 'Name: TestMatt' originally
    output_id = output_lines[4].split(' ')[2]  # User ID: 2 originally
    output_key = output_lines[5].split(' ')[2]  # API Key: ______ originally
    
    assert output_name == 'TestMatt'
    assert output_id == '2'

    # Can our user actually log in with the API key given?
    with app.app_context():
        assert validate_api_key(output_id, output_key)

def test_rotate_user_key(app, runner):
    """Tests the ability to rotate an API key from the CLI.
    """
    result = runner.invoke(rotate_user_key, input='1')
    output_lines = result.output.split('\n')

    new_key = output_lines[2].split('New API key is: ')[1]
    # Does the new key actually work?
    with app.app_context():
        assert validate_api_key(1, new_key)


def test_table_drop(app, runner):
    """Tests the ability to drop tables from the CLI.
    """
    result = runner.invoke(drop_tables, input="y")

    with app.app_context():
        assert not db.engine.has_table('link')
        assert not db.engine.has_table('user')