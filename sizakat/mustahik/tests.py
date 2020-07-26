import json

from datetime import date
from django.db.utils import IntegrityError
from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from sizakat.schema import schema

from .models import Mustahik


class MustahikModelTestCase(TestCase):
    def setUp(self):
        Mustahik.objects.create(
            name='mustahik',
            no_ktp='31751234567890',
            phone='081234567890',
            address='Jalan raya depok',
            province='Jawa Barat',
            regency='Depok',
            rt='003',
            rw='002',
            birthdate=date(1987, 6, 5),
            status=Mustahik.Status.MISKIN,
            family_size=4,
            description='desc'
        )

    def test_mustahik_creation(self):
        mustahik = Mustahik.objects.get(no_ktp='31751234567890')
        self.assertTrue(isinstance(mustahik, Mustahik))

    def test_no_ktp_mustahik_is_unique(self):
        with self.assertRaises(IntegrityError):
            Mustahik.objects.create(
                name='kihatsum',
                no_ktp='31751234567890',
                phone='08987654321',
                address='Jalan raya bogor',
                province='Jawa Barat',
                regency='Bogor',
                rt='002',
                rw='003',
                birthdate=date(1987, 4, 3),
                status=Mustahik.Status.MISKIN,
                family_size=1,
                description='no_ktp is unique'
            )


class MustahikGraphQLTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def setUp(self):
        Mustahik.objects.create(
            name='mustahik',
            no_ktp='31751234567890',
            phone='081234567890',
            address='Jalan raya depok',
            province='Jawa Barat',
            regency='Depok',
            rt='003',
            rw='002',
            birthdate=date(1987, 6, 5),
            status=Mustahik.Status.MISKIN,
            family_size=4,
            description='desc'
        )

    def test_mustahik_mutation_can_add_new_mustahik(self):
        no_ktp = '123891210121'
        response = self.query(
            '''
            mutation mustahikMutation($input: MustahikMutationInput!) {
                mustahikMutation(input: $input) {
                    mustahik {
                        id
                        name
                        noKtp
                        status
                        description
                    }
                    errors {
                        field
                        messages
                    }
                }
            }
            ''',
            op_name='mustahikMutation',
            input_data={
                "name": "jumat",
                "noKtp": no_ktp,
                "phone": "02132132180",
                "address": "jalan swadaya",
                "province": "jakarta",
                "regency": "manggarai",
                "rt": "001",
                "rw": "001",
                "birthdate": "1998-03-12",
                "status": "YATIM",
                "familySize": 3,
                "description": "anak yatim"
            }
        )

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)

        # Validate content
        content = json.loads(response.content)
        self.assertEqual(content['data']['mustahikMutation']
                         ['mustahik']['status'], 'YATIM')

        # Validate success save to db
        self.assertNotEqual(Mustahik.objects.count(), 0)
        mustahik = Mustahik.objects.get(no_ktp=no_ktp)
        self.assertEqual(mustahik.name, 'jumat')

    def test_mustahik_mutation_can_update_mustahik(self):
        mustahik = Mustahik.objects.get(no_ktp='31751234567890')
        mustahik_id = mustahik.pk
        old_desc = mustahik.description
        new_desc = 'keluarga tidak mampu'
        response = self.query(
            '''
            mutation mustahikMutation($input: MustahikMutationInput!) {
                mustahikMutation(input: $input) {
                    mustahik {
                        id
                        description
                    }
                    errors {
                        field
                        messages
                    }
                }
            }
            ''',
            op_name='mustahikMutation',
            input_data={
                "name": "mustahik",
                "noKtp": "31751234567890",
                "phone": "081234567890",
                "address": "Jalan raya depok",
                "province": "Jawa Barat",
                "regency": "Depok",
                "rt": "003",
                "rw": "002",
                "birthdate": "1987-06-05",
                "status": "MISKIN",
                "familySize": 4,
                "description": new_desc,
                "id": mustahik.pk
            }
        )

        # Validate success update desc mustahik
        mustahik = Mustahik.objects.get(no_ktp='31751234567890')
        self.assertNotEqual(mustahik.description, old_desc)
        self.assertEqual(mustahik.description, new_desc)

    def test_query_mustahik_should_return_list_of_mustahiks(self):
        response = self.query(
            '''
            query mustahiksQuery{
                mustahiks {
                    id,
                    name
                }
            }
            ''',
            op_name='mustahiksQuery'
        )

        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['mustahiks']), 1)
        self.assertEqual(content['data']['mustahiks'][0]['name'], 'mustahik')

    def test_query_mustahiks_if_statuses_is_set_should_return_list_of_mustahiks_with_coresponding_status(self):
        Mustahik.objects.create(
            name='test',
            no_ktp='11751234567890',
            phone='081234567890',
            address='Jalan raya depok',
            province='Jawa Barat',
            regency='Depok',
            rt='003',
            rw='002',
            birthdate=date(1987, 6, 5),
            status=Mustahik.Status.YATIM,
            family_size=4,
            description='desc'
        )

        response = self.query(
            '''
                query mustahiksQuery($statuses: [String]) {
                    mustahiks(statuses: $statuses) {
                        id,
                        name,
                        status
                    }
                }
            ''',
            op_name='mustahiksQuery',
            variables={'statuses': [Mustahik.Status.MISKIN]}
        )

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['mustahiks']), 1)

        for mustahik in content['data']['mustahiks']:
            self.assertEqual(mustahik['status'], Mustahik.Status.MISKIN)

    def test_query_mustahiks_if_statuses_is_provided_and_no_mustahiks_are_qualified_it_should_return_empty_list(self):
        response = self.query(
            '''
                query mustahiksQuery($statuses: [String]) {
                    mustahiks(statuses: $statuses) {
                        id,
                        name,
                        status
                    }
                }
            ''',
            op_name='mustahiksQuery',
            variables={'statuses': [Mustahik.Status.JANDA]}
        )

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['mustahiks']), 0)

    def test_mustahik_mutation_can_delete_mustahik(self):
        count = Mustahik.objects.count()
        mustahik = Mustahik.objects.get(no_ktp='31751234567890')
        mustahik_id = mustahik.pk
        response = self.query(
            '''
                mutation deleteMustahik($id: ID) {
                    deleteMustahik(id: $id) {
                        deleted
                        idMustahik
                        name
                        noKtp
                    }
                }
            ''',
            op_name='deleteMustahik',
            variables={'id': mustahik_id}
        )

        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertTrue(content['data']['deleteMustahik']['deleted'])
        self.assertEquals(Mustahik.objects.count(), count-1)

    def test_mustahik_query_can_read_detail_mustahik(self):
        mustahik = Mustahik.objects.get(no_ktp='31751234567890')
        mustahik_id = mustahik.pk
        response = self.query(
            '''
                query detailMustahikQuery($id:ID!){
                    mustahik(id:$id){
                        id
                        name
                        noKtp
                        phone
                        address
                        province
                        regency
                        rt
                        rw
                        birthdate
                        status
                        familySize
                        description
                    }
                }
            ''',
            op_name='detailMustahikQuery',
            variables={'id': mustahik_id}
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(len(content['data']), 1)
        self.assertEqual(content['data']['mustahik']['name'], 'mustahik')
        self.assertEqual(content['data']['mustahik']
                         ['noKtp'], '31751234567890')
        self.assertEqual(content['data']['mustahik']
                         ['address'], 'Jalan raya depok')

    def test_mustahiks_if_name_is_set_should_return_list_of_mustahiks_that_contain_the_name(self):
        Mustahik.objects.create(
            name='test',
            no_ktp='11751234567890',
            phone='081234567890',
            address='Jalan raya depok',
            province='Jawa Barat',
            regency='Depok',
            rt='003',
            rw='002',
            birthdate=date(1987, 6, 5),
            status=Mustahik.Status.YATIM,
            family_size=4,
            description='desc'
        )

        Mustahik.objects.create(
            name='eslu',
            no_ktp='22751234337899',
            phone='081234567890',
            address='Jalan depok',
            province='Jawa Timur',
            regency='Bondo',
            rt='003',
            rw='002',
            birthdate=date(1987, 6, 5),
            status=Mustahik.Status.YATIM,
            family_size=4,
            description='desc'
        )

        response = self.query(
            '''
            query mustahiks($nameContains:String){
                mustahiks(nameContains: $nameContains){
                    id,
                    name
                }
                
            }
            ''',
            op_name='mustahiks',
            variables={'nameContains': 'es'}
        )

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['mustahiks']), 2)
        self.assertEqual(
            content['data']['mustahiks'][0]['name'], 'test')
        self.assertEqual(
            content['data']['mustahiks'][1]['name'], 'eslu')

    def test_mustahiks_if_name_is_not_available_should_return_empty_list(self):
        response = self.query(
            '''
            query mustahiks($nameContains:String){
                mustahiks(nameContains: $nameContains){
                    id,
                    name
                }
                
            }
            ''',
            op_name='mustahiks',
            variables={'nameContains': '#'}
        )

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['mustahiks']), 0)
