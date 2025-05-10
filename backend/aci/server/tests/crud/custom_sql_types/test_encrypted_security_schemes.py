import base64

from sqlalchemy import text
from sqlalchemy.orm import Session

from aci.common import encryption
from aci.common.db.sql_models import App, AppConfiguration, Project
from aci.common.enums import HttpLocation, SecurityScheme, Visibility
from aci.common.schemas.security_scheme import OAuth2Scheme


def test_app_table_security_schemes_column_encryption(db_session: Session) -> None:
    """Test that App.security_schemes is correctly encrypted and decrypted."""
    # Given - Create test data
    expected_client_secret = "very_secret_value"
    expected_security_schemes = {
        SecurityScheme.OAUTH2: OAuth2Scheme(
            location=HttpLocation.HEADER,
            name="Authorization",
            prefix="Bearer",
            client_id="test_client_id",
            client_secret=expected_client_secret,
            scope="openid email profile",
            authorize_url="https://example.com/auth",
            access_token_url="https://example.com/access_token",
            refresh_token_url="https://example.com/refresh_token",
        ).model_dump()
    }

    # Given - Create and save App with security_schemes
    app = App(
        name="test_app",
        logo="https://example.com/logo.png",
        display_name="Test App",
        provider="test_provider",
        version="1.0.0",
        description="Test description",
        categories=["test"],
        visibility=Visibility.PUBLIC,
        active=True,
        security_schemes=expected_security_schemes,
        default_security_credentials_by_scheme={},
        embedding=[0.0] * 1024,
    )
    db_session.add(app)
    db_session.commit()

    # When - Clear session and retrieve the App
    db_session.expunge_all()
    retrieved_app = db_session.query(App).filter_by(name="test_app").first()
    assert retrieved_app is not None

    # Then - the app retrieved from the database should have the same client secret
    assert retrieved_app.security_schemes == expected_security_schemes
    assert (
        retrieved_app.security_schemes[SecurityScheme.OAUTH2]["client_secret"]
        == expected_client_secret
    )

    # Then - Verify the value is actually encrypted in the database
    raw_query = text("SELECT security_schemes FROM apps WHERE name = 'test_app'")
    result = db_session.execute(raw_query).first()
    raw_security_schemes = result[0] if result else None
    assert raw_security_schemes is not None
    assert isinstance(raw_security_schemes, dict)

    raw_client_secret = raw_security_schemes[SecurityScheme.OAUTH2]["client_secret"]
    assert raw_client_secret is not None
    assert raw_client_secret != expected_client_secret

    # Then - Decrypt the value and verify it matches the original value
    decrypted_client_secret = encryption.decrypt(base64.b64decode(raw_client_secret)).decode(
        "utf-8"
    )
    assert decrypted_client_secret == expected_client_secret


def test_app_configuration_table_security_scheme_overrides_column_encryption(
    dummy_app_aci_test: App,
    dummy_project_1: Project,
    db_session: Session,
) -> None:
    """Test that AppConfiguration.security_scheme_overrides is correctly encrypted and decrypted."""
    # Given - Create test data
    expected_client_secret = "app_config_secret_value"
    expected_security_scheme_overrides = {
        SecurityScheme.OAUTH2: OAuth2Scheme(
            location=HttpLocation.HEADER,
            name="Authorization",
            prefix="Bearer",
            client_id="test_client_id",
            client_secret=expected_client_secret,
            scope="openid email profile",
            authorize_url="https://example.com/auth",
            access_token_url="https://example.com/access_token",
            refresh_token_url="https://example.com/refresh_token",
        ).model_dump()
    }

    # Given - Create and save AppConfiguration with security_scheme_overrides
    app_config = AppConfiguration(
        project_id=dummy_project_1.id,
        app_id=dummy_app_aci_test.id,
        security_scheme=SecurityScheme.OAUTH2,
        security_scheme_overrides=expected_security_scheme_overrides,
        enabled=True,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.add(app_config)
    db_session.commit()

    # When - Clear session and retrieve the AppConfiguration
    app_config_id = app_config.id
    db_session.expunge_all()
    retrieved_app_config = db_session.query(AppConfiguration).filter_by(id=app_config_id).first()
    assert retrieved_app_config is not None

    # Then - the app config retrieved from the database should have the same client secret
    assert retrieved_app_config.security_scheme_overrides == expected_security_scheme_overrides
    assert (
        retrieved_app_config.security_scheme_overrides[SecurityScheme.OAUTH2]["client_secret"]
        == expected_client_secret
    )

    # Then - Verify the value is actually encrypted in the database
    raw_query = text("SELECT security_scheme_overrides FROM app_configurations WHERE id = :id")
    result = db_session.execute(raw_query, {"id": str(app_config_id)}).first()
    raw_security_scheme_overrides = result[0] if result else None
    assert raw_security_scheme_overrides is not None
    assert isinstance(raw_security_scheme_overrides, dict)

    raw_client_secret = raw_security_scheme_overrides[SecurityScheme.OAUTH2]["client_secret"]
    assert raw_client_secret is not None
    assert raw_client_secret != expected_client_secret

    # Then - Decrypt the value and verify it matches the original value
    decrypted_client_secret = encryption.decrypt(base64.b64decode(raw_client_secret)).decode(
        "utf-8"
    )
    assert decrypted_client_secret == expected_client_secret


def test_app_table_security_schemes_column_mutable_dict_detection(db_session: Session) -> None:
    """Test that App.security_schemes is correctly detected as a mutable dict, meaning
    when the first level fields of the json changed, SQLAlchemy will detect it as a change
    and save it to the database.
    """
    # Given - Create test data
    initial_authorize_url = "https://example.com/auth"
    security_schemes = {
        SecurityScheme.OAUTH2: OAuth2Scheme(
            location=HttpLocation.HEADER,
            name="Authorization",
            prefix="Bearer",
            client_id="test_client_id",
            client_secret="very_secret_value",
            scope="openid email profile",
            authorize_url=initial_authorize_url,
            access_token_url="https://example.com/access_token",
            refresh_token_url="https://example.com/refresh_token",
        ).model_dump()
    }

    # Given - Create and save App with security_schemes
    app = App(
        name="test_app",
        logo="https://example.com/logo.png",
        display_name="Test App",
        provider="test_provider",
        version="1.0.0",
        description="Test description",
        categories=["test"],
        visibility=Visibility.PUBLIC,
        active=True,
        security_schemes=security_schemes,
        default_security_credentials_by_scheme={},
        embedding=[0.0] * 1024,
    )
    db_session.add(app)
    db_session.commit()

    # When - Update the security_schemes
    new_authorize_url = "https://example.com/new_auth"
    new_security_schemes = app.security_schemes[SecurityScheme.OAUTH2].copy()
    new_security_schemes["authorize_url"] = new_authorize_url

    app.security_schemes[SecurityScheme.OAUTH2] = new_security_schemes
    db_session.commit()

    # Then - The change is detected and saved to the database
    db_session.expunge_all()
    retrieved_app = db_session.query(App).filter_by(name="test_app").first()
    assert retrieved_app is not None
    assert (
        retrieved_app.security_schemes[SecurityScheme.OAUTH2]["authorize_url"] == new_authorize_url
    )


def test_app_configuration_table_security_scheme_overrides_column_mutable_dict_detection(
    dummy_app_aci_test: App,
    dummy_project_1: Project,
    db_session: Session,
) -> None:
    """Test that AppConfiguration.security_scheme_overrides is correctly detected as a mutable dict, meaning
    when the first level fields of the json changed, SQLAlchemy will detect it as a change
    and save it to the database.
    """
    # Given - Create and save AppConfiguration with security_scheme_overrides
    initial_authorize_url = "https://example.com/auth"
    security_scheme_overrides = {
        SecurityScheme.OAUTH2: OAuth2Scheme(
            location=HttpLocation.HEADER,
            name="Authorization",
            prefix="Bearer",
            client_id="test_client_id",
            client_secret="very_secret_value",
            scope="openid email profile",
            authorize_url=initial_authorize_url,
            access_token_url="https://example.com/access_token",
            refresh_token_url="https://example.com/refresh_token",
        ).model_dump()
    }
    app_config = AppConfiguration(
        project_id=dummy_project_1.id,
        app_id=dummy_app_aci_test.id,
        security_scheme=SecurityScheme.OAUTH2,
        security_scheme_overrides=security_scheme_overrides,
        enabled=True,
        all_functions_enabled=True,
        enabled_functions=[],
    )
    db_session.add(app_config)
    db_session.commit()

    # When - Update the security_scheme_overrides
    new_authorize_url = "https://example.com/new_auth"
    new_security_scheme_overrides = app_config.security_scheme_overrides[
        SecurityScheme.OAUTH2
    ].copy()
    new_security_scheme_overrides["authorize_url"] = new_authorize_url

    app_config.security_scheme_overrides[SecurityScheme.OAUTH2] = new_security_scheme_overrides
    db_session.commit()

    # Then - The change is detected and saved to the database
    app_config_id = app_config.id
    db_session.expunge_all()
    retrieved_app_config = db_session.query(AppConfiguration).filter_by(id=app_config_id).first()
    assert retrieved_app_config is not None
    assert (
        retrieved_app_config.security_scheme_overrides[SecurityScheme.OAUTH2]["authorize_url"]
        == new_authorize_url
    )
