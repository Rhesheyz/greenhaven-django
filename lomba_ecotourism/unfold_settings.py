from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "Green Haven Management",
    "SITE_HEADER": "Green Haven Management",
    "SITE_URL": "https://greenhaven.rwiconsulting.tech/destinations",
    
    "THEME": None,  
    "SHOW_HISTORY": True,  
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_LANGUAGES": True,
    
    "LANGUAGES": [
        ("en", "English"),
        ("id", "Indonesian"),
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Content Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Destinations"),
                        "icon": "tour",
                        "link": reverse_lazy("admin:destinations_destinations_changelist"),
                    },
                    {
                        "title": _("Flora"),
                        "icon": "local_florist",
                        "link": reverse_lazy("admin:flora_flora_changelist"),
                    },
                    {
                        "title": _("Fauna"),
                        "icon": "pets",
                        "link": reverse_lazy("admin:fauna_fauna_changelist"),
                    },
                    {
                        "title": _("Culinary"),
                        "icon": "restaurant_menu",
                        "link": reverse_lazy("admin:kuliner_kuliner_changelist"),
                    },
                    {
                        "title": _("Health"),
                        "icon": "medical_services",
                        "link": reverse_lazy("admin:health_health_changelist"),
                    },
                ],
            },
            {
                "title": _("Hotel Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Hotel"),
                        "icon": "hotel",  # Sesuaikan ikon dengan Unfold Icons
                        "link": reverse_lazy("admin:hotel_hotel_changelist"),
                    },
                    {
                        "title": _("Room Detail"),
                        "icon": "bed",  # Sesuaikan dengan Unfold Icons
                        "link": reverse_lazy("admin:hotel_detailroom_changelist"),
                    },
                ],
            },
            {
                "title": _("Blog Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Category Article"),
                        "icon": "list",  # Sesuaikan ikon dengan Unfold Icons
                        "link": reverse_lazy("admin:artikel_kategoriartikel_changelist"),
                    },
                    {
                        "title": _("Article"),
                        "icon": "article",  # Sesuaikan dengan Unfold Icons
                        "link": reverse_lazy("admin:artikel_artikel_changelist"),
                    },
                ],
            },
            {
                "title": _("Analytics"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Request Log"),
                        "icon": "analytics",
                        "link": reverse_lazy("admin:analytics_requestlog_changelist"),
                    },
                    {
                        "title": _("Compliance Log"),
                        "icon": "security",
                        "link": reverse_lazy("admin:analytics_compliancelog_changelist"),
                    },
                    {
                        "title": _("Custom Event"),
                        "icon": "event_note",
                        "link": reverse_lazy("admin:analytics_customevent_changelist"),
                    },
                    {
                        "title": _("AI Analytics"),
                        "icon": "insights",
                        "link": reverse_lazy("admin:ai_aianalytics_changelist"),
                    },
                    {
                        "title": _("AI Feedback Analytics"),
                        "icon": "feedback",
                        "link": reverse_lazy("admin:ai_aifeedbackanalytics_changelist"),
                    }
                ],
            },
            {
                "title": _("AI Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Chatbot Intents"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:ai_intents_changelist"),
                    },
                    {
                        "title": _("Chat Feedback"),
                        "icon": "rate_review",
                        "link": reverse_lazy("admin:ai_chatfeedback_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Authentication"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
    "COLORS": { 
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "75 85 99",
            "default-dark": "209 213 219",
            "important-light": "17 24 39",
            "important-dark": "243 244 246",
        },
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
}
