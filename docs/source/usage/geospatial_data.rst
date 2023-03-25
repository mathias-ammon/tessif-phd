***************
Geospatial Data
***************

In Tessif geospatial data is represented as ``Latitude`` and ``Longitude`` and is interpreted (by convention) as stated in degrees.

Each energy system node - or more programatically speaking - each instance of tessif's :ref:`Models_Tessif_Concept_ESC` stores its geographical location. The information is stored inside a :mod:`~typing.NamedTuple` unique for each energy system component called :mod:`~tessif.frused.namedtuples.Uid` and is accessible via ``uid.latitude`` and ``uid.longitude`` respectively.

For i.e. a :class:`~tessif.model.components.Source` instance this would be realised like follows::

  >>> from tessif.model.components import Source
  >>> source_instance = Source(
  ...     name='wind_mill', outputs=('electricity',),
  ...     latitude=53.46, longitude=9.969309)

And consequently accessed like::

  >>> print('latitude:', source_instance.uid.latitude)
  latitude: 53.46
  >>> print('longitude:', source_instance.uid.longitude)
  longitude: 9.969309

.. note::     
    The fact that the geographical location is part of an energy system component's unique identifier makes it possible to use exactly the same node several times within the same simulation setup, given their geographical locations differ.
    
