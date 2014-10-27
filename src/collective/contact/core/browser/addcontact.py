from AccessControl import getSecurityManager
from zope.component import getUtility, queryAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.event import notify
from zope.interface import implements, Interface
from zope.publisher.browser import BrowserView

from z3c.form import field, form, button
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm, HIDDEN_MODE,\
    DISPLAY_MODE

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from five import grok

from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.events import AddCancelledEvent
from plone.dexterity.i18n import MessageFactory as DMF
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.supermodel import model

from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.source import ContactSourceBinder
from collective.contact.widget.interfaces import IContactWidgetSettings

from collective.contact.core import _
from collective.contact.core.content.person import IPerson
from collective.contact.core.behaviors import IContactDetails


class ICustomSettings(Interface):
    """You can overrides those methods by writing an adapter to IDirectory.
    If none is found, it fallbacks to the implementation in
    ContactWidgetSettings utility.
    """
    def add_url_for_portal_type(self, directory_url, portal_type):
        """Return add url for the specified portal_type.
        """


class ContactWidgetSettings(grok.GlobalUtility):
    grok.provides(IContactWidgetSettings)
    grok.implements(ICustomSettings)

    def add_url_for_portal_type(self, directory_url, portal_type):
        url = '%s/++add++%s' % (directory_url, portal_type)
        return url

    def add_contact_infos(self, widget):
        source = widget.bound_source
        criteria = source.selectable_filter.criteria
        addlink_enabled = widget.field.addlink
        portal_types = criteria.get('portal_type', [])

        catalog = getToolByName(widget.context, 'portal_catalog')
        results = catalog.unrestrictedSearchResults(portal_type='directory')
        actions = []
        if len(results) == 0:
            addlink_enabled = False
        else:
            directory = results[0].getObject()
            sm = getSecurityManager()
            if not sm.checkPermission("Add portal content", directory):
                addlink_enabled = False

        close_on_click = True
        if addlink_enabled:
            directory_url = directory.absolute_url()
            if len(portal_types) == 1:
                portal_type = portal_types[0]
                if portal_type == 'held_position' and not IPerson.providedBy(widget.context):
                    url = "%s/@@add-contact" % directory_url
                    type_name = _(u"Contact")
                    label = _(u"Create ${name}", mapping={'name': type_name})
                    if getattr(source, 'relations', None):
                        # if we have a relation, with an organization or a position
                        # we will pre-complete contact creation form
                        if 'position' in source.relations:
                            related_path = source.relations['position']
                            related_to = api.content.get(related_path)
                            if related_to is not None:
                                label = _(u"Create ${name} (${position})",
                                          mapping={'name': type_name,
                                                   'position': related_to.Title()})
                                url += '?oform.widgets.%s=%s' % (related_to.portal_type,
                                                   '/'.join(related_to.getPhysicalPath()))

                    action = {'url': url, 'label': label,
                              'klass': 'addnew',
                              'formselector': '#oform',
                              'closeselector': '[name="oform.buttons.cancel"]'}
                    actions.append(action)
                    close_on_click = False
                else:
                    custom_settings = queryAdapter(directory, ICustomSettings, default=self)
                    url = custom_settings.add_url_for_portal_type(directory_url, portal_type)
                    fti = getUtility(IDexterityFTI, name=portal_type)
                    type_name = fti.Title()
                    label = _(u"Create ${name}", mapping={'name': type_name})
                    action = {'url': url, 'label': label}
                    actions.append(action)
            else:
                if len(portal_types) == 2 and \
                        'organization' in portal_types and \
                        'position' in portal_types:
                    url = "%s/@@add-organization" % directory_url
                    type_name = _(u"organization/position")
                else:
                    url = "%s/@@add-contact" % directory_url
                    type_name = _(u"Contact")

                close_on_click = False
                label = _(u"Create ${name}", mapping={'name': type_name})
                action = {'url': url, 'label': label,
                          'klass': 'addnew',
                          'formselector': '#oform',
                          'closeselector': '[name="oform.buttons.cancel"]'}
                actions.append(action)

        return {'actions': actions,
                'close_on_click': close_on_click,
                'formatItem': """function(row, idx, count, value) {
return '<img src="' + portal_url + '/' + row[2] + '_icon.png'
 +'" /> ' + row[1] }"""
                }


class MasterSelectAddContactProvider(BrowserView):
    implements(IContentProvider)

    def __init__(self, context, request, view):
        super(MasterSelectAddContactProvider, self).__init__(context, request)
        self.__parent__ = view

    def update(self):
        pass

    def render(self):
        # If we fill organization and person, show position and held position fields
        return ""
        return """<script type="text/javascript">
$(document).ready(function() {

  var o = $('#oform');
  o.find('div[id$=held_position-position]').hide();
  var position_fields = '#formfield-oform-widgets-position,div[id*=held_position]';
  if (!(o.find('input[name="oform.widgets.person"]').length >= 1 &&
        o.find('input[name="oform.widgets.organization"]').length >= 1)) {
      o.find(position_fields).hide();
 }

  function get_selected_organization(form) {
    return contactswidget.get_selected_contact(form, 'oform.widgets.organization');
  }

  o.find('#oform-widgets-organization-input-fields').delegate('input', 'change', function(e){
    var form = $(this).closest('form');
    var orga = get_selected_organization(form);
    var add_organization_url, addneworga, add_text;

    addneworga = o.find('#oform-widgets-organization-autocomplete .addnew');
    addneworga.each(function(){
        if (!addneworga.data('pbo').original_src) {
            addneworga.data('pbo').original_src = addneworga.data('pbo').src;
            addneworga.data('pbo').original_text = addneworga.text();
        }
        if (orga.token == '--NOVALUE--') {
          o.find(position_fields).hide();
          add_organization_url = addneworga.data('pbo').original_src;
          add_text = addneworga.data('pbo').original_text;
        } else {
          // update add new orga link to add sub orga
          add_organization_url = portal_url + orga.path + '/++add++organization';
          add_text = addneworga.data('pbo').original_text + ' dans ' + orga.title;
        }
        addneworga.data('pbo').src = add_organization_url;
        addneworga.text(add_text);
    })

    // update position autocomplete field
    o.find('#formfield-oform-widgets-position > .fieldErrorBox').text('Recherchez ou ajoutez une fonction dans "' + orga.title + '".');
    o.find("#oform-widgets-position-widgets-query")
        .setOptions({extraParams: {path: orga.token}}).flushCache();

    // update add new position url
    var add_position_url = portal_url + orga.path + '/++add++position';
    o.find('#oform-widgets-position-autocomplete .addnew').each(function(){
        jQuery(this).data('pbo').src = add_position_url;
    })

    // show position and held position fields if orga and person are selected
    if ((!o.find('#formfield-oform-widgets-person').length || o.find('input[name="oform.widgets.person"]').length >= 1) &&
        o.find('input[name="oform.widgets.organization"]').length >= 1 &&
        orga.token != '--NOVALUE--') {
      o.find(position_fields).show('slow');
      o.find('div[id$=held_position-position]').hide();
    }
  });

  o.find('#oform-widgets-person-input-fields').delegate('input', 'change', function(e){
    if (o.find('input[name="oform.widgets.person"]').length >= 1 &&
        o.find('input[name="oform.widgets.organization"]').length >= 1) {
      o.find(position_fields).show('slow');
      o.find('div[id$=held_position-position]').hide();
    }
  });

  o.find('#oform-widgets-position-widgets-query').setOptions({minChars: 0});
  o.find('#oform-widgets-position-widgets-query').focus(function(e){
    $(this).trigger('click');
  });

  // If organization was pre filled, we need to trigger the change event.
  o.find('#oform-widgets-organization-input-fields input').trigger('change');

});
</script>
"""


class IAddContact(model.Schema):
    organization = ContactChoice(
            title=_(u"Organization"),
            required=False,
            description=_(u"Select the organization where the person holds the position"),
            source=ContactSourceBinder(portal_type="organization"))

    person = ContactChoice(
            title=_(u"Person"),
            description=_(u"Select the person who holds the position"),
            required=True,
            source=ContactSourceBinder(portal_type="person"))

    position = ContactChoice(
            title=_(u"Position"),
            required=False,
            description=_(u"Select the position held by this person in the selected organization"),
            source=ContactSourceBinder(portal_type="position"))


class AddContact(DefaultAddForm, form.AddForm):
    implements(IFieldsAndContentProvidersForm)
    contentProviders = ContentProviders(['organization-ms'])
#    contentProviders['organization-ms'] = MasterSelectAddContactProvider
    contentProviders['organization-ms'].position = -1
    label = _(u"Create ${name}", mapping={'name': _(u"Contact")})
    description = _(u"A contact is a position held by a person in an organization")
    schema = IAddContact
    portal_type = 'held_position'
    prefix = 'oform'

    @property
    def additionalSchemata(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        schema = fti.lookupSchema()
        # save the schema name to be able to remove a field afterwards
        self._schema_name = schema.__name__
        return (schema,)

    def updateFieldsFromSchemata(self):
        super(AddContact, self).updateFieldsFromSchemata()
        # IHeldPosition and IAddContact have both a field named position
        # hide the one from IHeldPosition
        # TODO: there is no hidden template for autocomplete widget,
        # we hide it in javascript for now.
        self.fields[self._schema_name + '.position'].mode = HIDDEN_MODE
        hp_fti = api.portal.get_tool('portal_types').held_position
        if IContactDetails.__identifier__ in hp_fti.behaviors:
            self.fields += field.Fields(IContactDetails)

    def updateWidgets(self):
        super(AddContact, self).updateWidgets()
        for widget in self.widgets.values():
            if getattr(widget, 'required', False):
                # This is really a hack to not have required field errors
                # but have the visual required nevertheless.
                # We need to revert this after updateActions
                # because this change impact the held position form
                widget.field.required = False

        if 'parent_address' in self.widgets:
            self.widgets['parent_address'].mode = DISPLAY_MODE

    def update(self):
        super(AddContact, self).update()
        # revert required field changes
        for widget in self.widgets.values():
            if getattr(widget, 'required', False):
                widget.field.required = True

    @button.buttonAndHandler(_('Add'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            IStatusMessage(self.request).addStatusMessage(DMF(u"Item created"),
                                                          "info")

    @button.buttonAndHandler(DMF(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(DMF(u"Add New Item operation cancelled"),
                                                      "info")
        self.request.response.redirect(self.nextURL())
        notify(AddCancelledEvent(self.context))

    def createAndAdd(self, data):
        if data['person'] is None and data['organization'] is None:
            return
        elif data['organization'] is not None and data['person'] is None:
            self.request.response.redirect(data['organization'].absolute_url())
            self._finishedAdd = True
            return
        elif data['person'] is not None and data['organization'] is None:
            self.request.response.redirect(data['person'].absolute_url())
            self._finishedAdd = True
            return
        else:
            return super(AddContact, self).createAndAdd(data)

    def create(self, data):
        self._container = data.pop('person')
        position = data.pop('position')
        orga = data.pop('organization')
        if position is None:
            position = orga

        data[self._schema_name + '.position'] = position
        return super(AddContact, self).create(data)

    def add(self, obj):
        container = self._container
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        new_object = addContentToContainer(container, obj)

        if fti.immediate_view:
            self.immediate_view = "%s/%s/%s" % (container.absolute_url(),
                                                new_object.id,
                                                fti.immediate_view,)
        else:
            self.immediate_view = "%s/%s" % (container.absolute_url(),
                                             new_object.id)


class AddContactFromOrganization(AddContact):
    def updateWidgets(self):
        if 'oform.widgets.organization' not in self.request.form:
            self.request.form['oform.widgets.organization'] = '/'.join(
                    self.context.getPhysicalPath())
        super(AddContactFromOrganization, self).updateWidgets()


class AddContactFromPosition(AddContact):
    def updateWidgets(self):
        organization = self.context.get_organization()
        if 'oform.widgets.organization' not in self.request.form:
            self.request.form['oform.widgets.organization'] = '/'.join(
                    organization.getPhysicalPath())

        if 'oform.widgets.position' not in self.request.form:
            self.request.form['oform.widgets.position'] = '/'.join(
                    self.context.getPhysicalPath())

        super(AddContactFromPosition, self).updateWidgets()


class AddOrganization(form.AddForm):
    implements(IFieldsAndContentProvidersForm)
    contentProviders = ContentProviders(['organization-ms'])
    contentProviders['organization-ms'].position = 2
    label = _(u"Create ${name}", mapping={'name': _(u"organization/position")})
    description = u""
    prefix = 'oform'
    fields = field.Fields(IAddContact).select('organization', 'position')

    def updateWidgets(self):
        super(AddOrganization, self).updateWidgets()
        self.widgets['organization'].label = _(
                 'help_add_organization_or_position_organization',
                 "Please fill the organization first "
                 "and then eventually select position")

    @button.buttonAndHandler(_('Add'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        self._finishedAdd = True
        if data['position'] is not None:
            self.request.response.redirect(data['position'].absolute_url())
            return
        elif data['organization'] is not None:
            self.request.response.redirect(data['organization'].absolute_url())
            return

    @button.buttonAndHandler(DMF(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        pass
