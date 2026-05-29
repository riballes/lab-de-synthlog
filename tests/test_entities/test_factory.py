"""Tests for entity factory determinism and correctness."""

from synthlog.entities import EntityFactory, EntityPool


class TestEntityFactory:
    def test_deterministic_output(self) -> None:
        pool1 = EntityFactory(seed=42).create_pool(num_users=5)
        pool2 = EntityFactory(seed=42).create_pool(num_users=5)
        assert [u.id for u in pool1.users] == [u.id for u in pool2.users]
        assert [u.login for u in pool1.users] == [u.login for u in pool2.users]

    def test_different_seeds_differ(self) -> None:
        pool1 = EntityFactory(seed=42).create_pool(num_users=5)
        pool2 = EntityFactory(seed=99).create_pool(num_users=5)
        assert [u.id for u in pool1.users] != [u.id for u in pool2.users]

    def test_user_id_prefix(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        for user in pool.users:
            assert user.id.startswith("00u")
            assert len(user.id) == 23  # 3 prefix + 20 random

    def test_app_id_prefix(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_apps=3)
        for app in pool.apps:
            assert app.id.startswith("0oa")

    def test_group_id_prefix(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_groups=2)
        for group in pool.groups:
            assert group.id.startswith("00g")

    def test_user_fields_populated(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        for user in pool.users:
            assert user.login
            assert "@" in user.login
            assert user.display_name
            assert user.email == user.login
            assert user.department
            assert user.title
            assert user.primary_device_id
            assert user.primary_network_id
            assert len(user.mfa_factors) >= 1

    def test_network_has_geo(self) -> None:
        pool = EntityFactory(seed=42).create_pool()
        for net in pool.networks:
            assert net.ip_address
            assert net.city
            assert net.country
            assert net.as_number > 0

    def test_pool_count(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=10, num_apps=4, num_groups=3)
        assert len(pool.users) == 10
        assert len(pool.apps) == 4
        assert len(pool.groups) == 3

    def test_first_group_has_all_users(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_groups=2)
        all_user_ids = {u.id for u in pool.users}
        assert set(pool.groups[0].member_ids) == all_user_ids


class TestEntityPoolPersistence:
    def test_json_roundtrip(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3, num_apps=2, num_groups=1)
        json_str = pool.to_json()
        restored = EntityPool.from_json(json_str)

        assert len(restored.users) == len(pool.users)
        assert len(restored.apps) == len(pool.apps)
        assert len(restored.groups) == len(pool.groups)

        for orig, rest in zip(pool.users, restored.users):
            assert orig.id == rest.id
            assert orig.login == rest.login
            assert orig.mfa_factors == rest.mfa_factors

    def test_pool_lookup(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        user = pool.users[0]
        assert pool.get_user(user.id) is user

    def test_pool_lookup_missing(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        try:
            pool.get_user("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass
