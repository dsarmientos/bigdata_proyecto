from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'politico.views.home', name='home'),
    url(r'^treemap/$', 'politico.views.treemap', name='treemap'),
    url(r'^combochar/$', 'politico.views.combochart', name='combochart'),
    url(r'^congresista/(\d+)$', 'politico.views.perfil_congresista', name='perfil_congresista'),
    url(r'^buscar/$', 'politico.views.buscar', name='buscar'),
    # url(r'^politico/', include('politico.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

## Serve static media in DEBUG mode
from django.conf import settings
if settings.DEBUG:
    import os
    PARENT_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.path.pardir))
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(PARENT_DIR, '/static/')}),
   )