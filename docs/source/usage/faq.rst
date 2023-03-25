.. _FAQ:

***
FAQ
***

Following sections try to provide a first clue on how to deal with commonly encountered issues.


.. contents::
   :local:

.. _FAQ_Different_Results:

Why do the results of my energy system differ so much among models?
*******************************************************************

You might utilize Combined Heat and Power (CHP) plants. Those are realised quite differently among models. There are two posiible apporaches to deal with that:

1. Interpret the difference in modeling this component as the info you are actually looking for. Meaning using your specific energy system with the models supported may just lead to this ambiguity, or, positively stated: This is the result deviation that is to be expexted. Which could mean, that a certain model may not be suited so well to your use case.

2. Check the parameterization of your energy system. Maybe the :ref:`Usage_Comparing_Caveats_CHP` section of the collected :ref:`Usage_Comparing_Caveats` can help.

My expansion problem does not solve correctly, why?
***************************************************

 - This might have many reasons. Probably the most common issue is explained in :ref:`Usage_Comparing_Caveats_Expansion` inside the of the collected :ref:`Usage_Comparing_Caveats` section.


Why does my pypsa-model do not respect the co2 emission limit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are three notable differences in the implementation of pypsa in regards to
co2 emissions:

  1. Pypsa does not report the total amount of emissions.
  2. StorageUnits actually store emissions, if their carrier has some emissions
     allocated.
  3. Link components do not respect their carrier and therfor can not respect
     the subsequet emissions. This is especially problematic since it is
     recommended by the developers to be expanded and used as chps and power2x
     alternatives. The former problem can be circumvented by reallocating the
     chp emissions to a generator feeding the chp. The latter however can not
     be rectified in a similar manner (at least to the lead authors current
     knowledge)

Point one makes it difficult to track the points of deviation. Point two and
three, in conjunction with tessifs co2 emission allocation, may lead to the
transformed pypsa model not interpreting the emissions as intented by tessif
and therfor simingly ignoring the imposed limit. This however is not
necissarily a fault on the side of the PyPSA interface but rather a large
difference between PyPSA and tessif.   
