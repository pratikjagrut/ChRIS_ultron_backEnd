
import os

from django.db import models
from django.conf import settings

from feeds.models import Feed, FeedFile


TYPE_CHOICES = [("string", "String values"), ("float", "Float values"),
                ("boolean", "Boolean values"), ("integer", "Integer values")]

TYPES = {'string': str, 'integer': int, 'float': float, 'boolean': bool}

PLUGIN_TYPE_CHOICES = [("ds", "Data plugin"), ("fs", "Filesystem plugin")]

STATUS_TYPES = ['started', 'running-on-remote', 'finished-on-remote']

class Plugin(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(choices=PLUGIN_TYPE_CHOICES, default='ds', max_length=4)

    class Meta:
        ordering = ('type',)

    def __str__(self):
        return self.name


class PluginParameter(models.Model):
    name = models.CharField(max_length=100)
    optional = models.BooleanField(default=True)
    default = models.CharField(max_length=200, blank=True)
    type = models.CharField(choices=TYPE_CHOICES, default='string', max_length=10)
    help = models.TextField(blank=True)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE,
                               related_name='parameters')
    
    class Meta:
        ordering = ('plugin',)

    def __str__(self):
        return self.name
    

class PluginInstance(models.Model):
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default=STATUS_TYPES[0])
    previous = models.ForeignKey("self", on_delete=models.CASCADE, null=True,
                                 related_name='next')
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='instances')
    owner = models.ForeignKey('auth.User')
    
    class Meta:
        ordering = ('start_date',)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        """
        Overriden to save a new feed to the DB the first time the instance is saved.
        """
        super(PluginInstance, self).save(*args, **kwargs)
        if not hasattr(self, 'feed') and self.plugin.type=='fs':
            self._save_feed()
            
    def _save_feed(self):
        """
        Custom method to create and save a new feed to the DB.
        """
        feed = Feed()
        feed.plugin_inst = self;
        feed.save()
        feed.owner = [self.owner]
        feed.save()

    def get_output_path(self):
        """
        Custom method to get the output directory for files generated by
        the plugin instance object.
        """
        # 'fs' plugins will output files to:
        # MEDIA_ROOT/<username>/feed_<id>/plugin_name_plugin_inst_<id>/data
        # 'ds' plugins will output files to:
        # MEDIA_ROOT/<username>/feed_<id>/...
        #/previous_plugin_name_plugin_inst_<id>/plugin_name_plugin_inst_<id>/data
        current = self
        path = '/{0}_{1}/data'.format(current.plugin.name, current.id)
        while not current.plugin.type == 'fs':
            current = current.previous
            path = '/{0}_{1}'.format(current.plugin.name, current.id) + path
        root = settings.MEDIA_ROOT
        username = self.owner.username
        output_path = '{0}/{1}/feed_{2}'.format(root, username, current.feed.id) + path
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        return output_path

    def register_output_files(self):
        """
        Custom method to register files generated by the plugin instance object
        with the REST API.
        """
        current = self
        while not current.plugin.type == 'fs':
            current = current.previous
        feed = current.feed
        output_path = self.get_output_path()
        for (dirpath, dirnames, filenames) in os.walk(output_path):
            for name in filenames:
                feedfile = FeedFile(plugin_inst=self)
                feedfile.fname.name = os.path.join(dirpath, name)
                feedfile.save()
                feedfile.feed = [feed]
                feedfile.save()
        
        
class StringParameter(models.Model):
    value = models.CharField(max_length=200, blank=True)
    plugin_inst = models.ForeignKey(PluginInstance, on_delete=models.CASCADE,
                                    related_name='string_param')
    plugin_param = models.ForeignKey(PluginParameter, on_delete=models.CASCADE,
                                     related_name='string_inst')

    def __str__(self):
        return self.value
    
    
class IntParameter(models.Model):
    value = models.IntegerField()
    plugin_inst = models.ForeignKey(PluginInstance, on_delete=models.CASCADE,
                                    related_name='int_param')
    plugin_param = models.ForeignKey(PluginParameter, on_delete=models.CASCADE,
                                     related_name='int_inst')

    def __str__(self):
        return str(self.value)
    

class FloatParameter(models.Model):
    value = models.FloatField()
    plugin_inst = models.ForeignKey(PluginInstance, on_delete=models.CASCADE,
                                    related_name='float_param')
    plugin_param = models.ForeignKey(PluginParameter, on_delete=models.CASCADE,
                                     related_name='float_inst')

    def __str__(self):
        return str(self.value)


class BoolParameter(models.Model):
    value = models.BooleanField(default=False, blank=True)
    plugin_inst = models.ForeignKey(PluginInstance, on_delete=models.CASCADE,
                                    related_name='bool_param')
    plugin_param = models.ForeignKey(PluginParameter, on_delete=models.CASCADE,
                                     related_name='bool_inst')

    def __str__(self):
        return str(self.value)



