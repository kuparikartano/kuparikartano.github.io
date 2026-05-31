---
layout: default
title: Jätteiden keräys
permalink: /jate-kerays
---


{% assign containers = site.data.trash.containers %}
{% if containers and containers.size > 0 %}
<table class="trash-table">
  <tr>
    <td>Jätelaji</td>
    <td>Arvioitu tyhjennys</td>
    <td>Tyhjennysväli</td>
  </tr>
{% for c in containers %}
  <tr>
    <td>{{ c.waste_type }}</td>
    <td>{{ c.next_collection_date_short }}</td>
    <td>{{ c.collection_interval }}</td>
  </tr>
{% endfor %}
    <td>Paperi</td>
    <td>ei tiedossa</td>
    <td>4 viikon välein maanantaisin</td>
</table>
{% else %}
Tietoja ei ole vielä haettu.
{% endif %}

Taloyhtiön jäteastiat sijaitsevat 4B-rappukäytävän päässä.
Perinteisesti korttelin yhtiöt tilaavat sekajätelavan kesäisin ja syksyisin.
