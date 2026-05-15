"""End-to-end tests covering all assignment endpoints + custom features + edge cases."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Note, NoteShare, PublicShareLink

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_success(self):
        r = self.client.post("/register", {"email": "a@b.com", "password": "Strongpass123"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(User.objects.filter(email="a@b.com").exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(email="a@b.com", password="Strongpass123")
        r = self.client.post("/register", {"email": "A@B.com", "password": "Strongpass123"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_register_invalid_email(self):
        r = self.client.post("/register", {"email": "not-an-email", "password": "Strongpass123"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_register_weak_password(self):
        r = self.client.post("/register", {"email": "a@b.com", "password": "short"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_login_success(self):
        User.objects.create_user(email="a@b.com", password="Strongpass123")
        r = self.client.post("/login", {"email": "a@b.com", "password": "Strongpass123"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access_token", r.data)

    def test_login_wrong_password(self):
        User.objects.create_user(email="a@b.com", password="Strongpass123")
        r = self.client.post("/login", {"email": "a@b.com", "password": "wrong"}, format="json")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.data.get("message"), "Invalid email or password")

    def test_login_unknown_user(self):
        r = self.client.post("/login", {"email": "x@y.com", "password": "anything"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_login_case_insensitive_email(self):
        User.objects.create_user(email="a@b.com", password="Strongpass123")
        r = self.client.post("/login", {"email": "A@B.com", "password": "Strongpass123"}, format="json")
        self.assertEqual(r.status_code, 200)


class NoteCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u1@b.com", password="Strongpass123")
        self.other = User.objects.create_user(email="u2@b.com", password="Strongpass123")
        self.client = APIClient()
        self._auth(self.user)

    def _auth(self, user):
        r = self.client.post("/login", {"email": user.email, "password": "Strongpass123"}, format="json")
        token = r.data["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_note(self):
        r = self.client.post("/notes", {"title": "Hello", "content": "World"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["title"], "Hello")
        self.assertTrue(r.data["is_owner"])

    def test_create_note_empty_title(self):
        r = self.client.post("/notes", {"title": "   ", "content": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_list_notes_only_own(self):
        Note.objects.create(owner=self.user, title="mine")
        Note.objects.create(owner=self.other, title="theirs")
        r = self.client.get("/notes")
        self.assertEqual(r.status_code, 200)
        results = r.data["results"] if isinstance(r.data, dict) else r.data
        titles = [n["title"] for n in results]
        self.assertIn("mine", titles)
        self.assertNotIn("theirs", titles)

    def test_get_note_unauthorized_returns_404(self):
        n = Note.objects.create(owner=self.other, title="secret")
        r = self.client.get(f"/notes/{n.id}")
        self.assertEqual(r.status_code, 404)

    def test_update_note(self):
        n = Note.objects.create(owner=self.user, title="t", content="c")
        r = self.client.put(f"/notes/{n.id}", {"title": "T2", "content": "C2"}, format="json")
        self.assertEqual(r.status_code, 200)
        n.refresh_from_db()
        self.assertEqual(n.title, "T2")

    def test_partial_update_note(self):
        n = Note.objects.create(owner=self.user, title="t", content="c")
        r = self.client.patch(f"/notes/{n.id}", {"color": "yellow", "is_pinned": True}, format="json")
        self.assertEqual(r.status_code, 200)
        n.refresh_from_db()
        self.assertEqual(n.color, "yellow")
        self.assertTrue(n.is_pinned)

    def test_delete_note(self):
        n = Note.objects.create(owner=self.user, title="t")
        r = self.client.delete(f"/notes/{n.id}")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Note.objects.filter(id=n.id).exists())

    def test_delete_other_users_note(self):
        n = Note.objects.create(owner=self.other, title="t")
        r = self.client.delete(f"/notes/{n.id}")
        self.assertEqual(r.status_code, 404)

    def test_unauthenticated_blocked(self):
        c = APIClient()
        r = c.get("/notes")
        self.assertEqual(r.status_code, 401)


class NoteSharingTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@x.com", password="Strongpass123")
        self.bob = User.objects.create_user(email="bob@x.com", password="Strongpass123")
        self.client = APIClient()
        r = self.client.post("/login", {"email": "alice@x.com", "password": "Strongpass123"}, format="json")
        self.alice_token = r.data["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        self.note = Note.objects.create(owner=self.alice, title="shared", content="hi")

    def test_share_with_user(self):
        r = self.client.post(f"/notes/{self.note.id}/share",
                             {"share_with_email": "bob@x.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(NoteShare.objects.filter(note=self.note, user=self.bob).exists())

    def test_shared_user_can_read(self):
        NoteShare.objects.create(note=self.note, user=self.bob, shared_by=self.alice)
        bob_client = APIClient()
        r = bob_client.post("/login", {"email": "bob@x.com", "password": "Strongpass123"}, format="json")
        bob_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access_token']}")
        r2 = bob_client.get(f"/notes/{self.note.id}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["title"], "shared")
        self.assertFalse(r2.data["is_owner"])

    def test_share_with_self_fails(self):
        r = self.client.post(f"/notes/{self.note.id}/share",
                             {"share_with_email": "alice@x.com"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_share_with_nonexistent_user(self):
        r = self.client.post(f"/notes/{self.note.id}/share",
                             {"share_with_email": "ghost@x.com"}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_share_idempotent(self):
        self.client.post(f"/notes/{self.note.id}/share",
                         {"share_with_email": "bob@x.com"}, format="json")
        r = self.client.post(f"/notes/{self.note.id}/share",
                             {"share_with_email": "bob@x.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(NoteShare.objects.filter(note=self.note).count(), 1)

    def test_only_owner_can_share(self):
        NoteShare.objects.create(note=self.note, user=self.bob, shared_by=self.alice)
        bob_client = APIClient()
        r = bob_client.post("/login", {"email": "bob@x.com", "password": "Strongpass123"}, format="json")
        bob_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access_token']}")
        r2 = bob_client.post(f"/notes/{self.note.id}/share",
                             {"share_with_email": "alice@x.com"}, format="json")
        self.assertEqual(r2.status_code, 403)

    def test_shared_user_cannot_delete(self):
        NoteShare.objects.create(note=self.note, user=self.bob, shared_by=self.alice)
        bob_client = APIClient()
        r = bob_client.post("/login", {"email": "bob@x.com", "password": "Strongpass123"}, format="json")
        bob_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access_token']}")
        r2 = bob_client.delete(f"/notes/{self.note.id}")
        self.assertEqual(r2.status_code, 403)


class PublicLinkTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="a@x.com", password="Strongpass123")
        self.note = Note.objects.create(owner=self.alice, title="public", content="readable")
        self.client = APIClient()
        r = self.client.post("/login", {"email": "a@x.com", "password": "Strongpass123"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access_token']}")

    def test_create_public_link(self):
        r = self.client.post(f"/notes/{self.note.id}/public-link", {}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("token", r.data)

    def test_public_read_without_auth(self):
        r = self.client.post(f"/notes/{self.note.id}/public-link", {}, format="json")
        token = r.data["token"]
        anon = APIClient()
        r2 = anon.get(f"/public/notes/{token}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["title"], "public")

    def test_revoke_public_link(self):
        r = self.client.post(f"/notes/{self.note.id}/public-link", {}, format="json")
        token = r.data["token"]
        self.client.delete(f"/notes/{self.note.id}/public-link")
        anon = APIClient()
        r2 = anon.get(f"/public/notes/{token}")
        self.assertEqual(r2.status_code, 404)

    def test_invalid_token(self):
        anon = APIClient()
        r = anon.get("/public/notes/nopenope")
        self.assertEqual(r.status_code, 404)

    def test_view_count_increments(self):
        r = self.client.post(f"/notes/{self.note.id}/public-link", {}, format="json")
        token = r.data["token"]
        anon = APIClient()
        anon.get(f"/public/notes/{token}")
        anon.get(f"/public/notes/{token}")
        link = PublicShareLink.objects.get(note=self.note)
        self.assertEqual(link.view_count, 2)


class SearchAndFiltersTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="s@x.com", password="Strongpass123")
        self.client = APIClient()
        r = self.client.post("/login", {"email": "s@x.com", "password": "Strongpass123"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access_token']}")
        Note.objects.create(owner=self.user, title="Grocery list", content="milk, eggs")
        Note.objects.create(owner=self.user, title="Meeting notes", content="quarterly review")
        Note.objects.create(owner=self.user, title="Recipe", content="pasta with milk")

    def test_search_title(self):
        r = self.client.get("/search?q=grocery")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)

    def test_search_content_multiple_hits(self):
        r = self.client.get("/search?q=milk")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 2)

    def test_search_requires_q(self):
        r = self.client.get("/search")
        self.assertEqual(r.status_code, 400)

    def test_pagination(self):
        for i in range(30):
            Note.objects.create(owner=self.user, title=f"n{i}")
        r = self.client.get("/notes?page_size=10")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["results"]), 10)
        self.assertIsNotNone(r.data["next"])


class MetaEndpointsTests(APITestCase):
    def test_about(self):
        r = self.client.get("/about")
        self.assertEqual(r.status_code, 200)
        self.assertIn("name", r.data)
        self.assertIn("email", r.data)
        self.assertIn("my features", r.data)

    def test_openapi(self):
        r = self.client.get("/openapi.json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data.get("openapi"), "3.0.3")
        self.assertIn("paths", r.data)
