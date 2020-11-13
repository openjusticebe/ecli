import graphene as g


COUNTRIES = ['BE']


class Country(g.ObjectType):
    id = g.String()


class Query(g.ObjectType):
    countries = g.List(Country)
    country = g.Field(Country, id=g.String())

    def resolve_country(root, info, country_id):
        data = {
            'id': country_id
        }
        return Country(**data)

    def resolve_countries(root, info):
        output = []
        for country in COUNTRIES:
            output.append({
                'id': country
            })
        return [Country(**c) for c in output]
