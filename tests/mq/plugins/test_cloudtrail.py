# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.cloudtrail import message


class TestCloudtrailPlugin():
    def setup(self):
        self.plugin = message()

    def test_nonexistent_source(self):
        msg = {
            'category': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_incorrect_source(self):
        msg = {
            'source': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_bad_details(self):
        msg = {
            'details': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert 'raw_value' not in msg['details']
        assert retmeta == {}

    def test_iamInstanceProfile(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iaminstanceprofile': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iaminstanceprofile': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_attribute(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_description(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'description': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'description': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_filter(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'filter': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'filter': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_role(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'role': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'role': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_additionaleventdata(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'additionaleventdata': {'afieldname': 'astringvalue'},
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'additionaleventdata': {
                    'raw_value': '{"afieldname": "astringvalue"}',
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_additionaleventdata_int(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'additionaleventdata': 1,
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'additionaleventdata': {
                    'raw_value': '1',
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_serviceeventdetails(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'serviceeventdetails': {'afieldname': 'astringvalue'},
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'serviceeventdetails': {
                    'raw_value': '{"afieldname": "astringvalue"}',
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_rule(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'rule': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'rule': {
                        'raw_value': '"astringvalue"',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_subnets(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'subnets': {'afieldname': 'astringvalue'},
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'subnets': {
                        'raw_value': '{"afieldname": "astringvalue"}',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_endpoint(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'endpoint': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'endpoint': {
                        'raw_value': '"astringvalue"',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_ebs_optimized(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'ebsoptimized': False,
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'ebsoptimized': {
                        'raw_value': 'false',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_securityGroups(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'securitygroups': ['astringvalue','anotherstringvalue']
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'securitygroups': {
                        'raw_value': '["astringvalue", "anotherstringvalue"]',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_disableApiTermination(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'disableapitermination': False
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'disableapitermination': {
                        'raw_value': 'false'
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_responseelements_lastModified(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'lastmodified': 'astringvalue'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'lastmodified': {
                        'raw_value': '"astringvalue"'
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_unusual(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'findings': {
                        'service': {
                            'additionalinfo': {
                                'unusual': 'astringvalue'
                            }
                        }
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'responseelements': {
                    'findings': {
                        'service': {
                            'additionalinfo': {
                                'unusual': {
                                    'raw_value': '"astringvalue"'
                                }
                            }
                        }
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_length_truncate(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'htmlpart': 'phdolIXPdTsHKfdoadpPfWXBkiSDWKGORPaHYlwvkuYHjPyeJDoaTswKpHSNqMMDQwHkEuCfKGqBZhZmjVEflKLRCwWcOErRISwyScnrhOAMoEjQsdbiNWqIZRwlxEqWvzxUugJJqTImGxsfysJcDGEnCamwkbyILnBChhsTFzvgUEKhiKPHdVNdjysJYLbgCIHCagKyfuXswFzmJHOwrEtMwIYqCnOteWBRwefYICdGbIWhlxzMwlIWGpMWgRZWzpoaqMQvTQDNJqTvkjxaUMIQbdmKDPjbZoFmaIjbDyDTwCkGCLzROyMHXdAqSRtBttUCvJtuyxvjlBXJdMzUDBtIPDjadBrqLDbKDdeFznFafjUhioHhcGgkdfIpoPGxWjrcZdWjJeQcRDwhXtekbNzFQbTtFJStNBXuVyZfKYYARtSiSMtLPEfqSOBrpyJlotaAcVutGgVhrVeVOaTBidaXwDjRUnfNOVgGiCkycpWsSCSCfozOwEiTunVdfPElCFyZXuOIRKFvEiTyuPExUcDVTNFsLvYmlOUqTvlMaWnXNpLQGpOTHSGxFPqlqsCeslnOKxvaXDKnQYufXatLmqFLygOsfbUsbbUWPEqyjUrtaEfXpxDwljeSYOTsgJllZlfWRjqtOKGwpKpyKewHNUWyJestNIbsWSvVQXMETeDacivvIbuqtIZbBXSQkYJNjmmYqnJWRXtLyqDKkzGegfHXWmIVfuXhHCqzfNfXNsRpZNeXhdEQqlcromCrPmYKkOQvrqqpXxaNDEoAkMKSVOHPcQEMVKjXQhMJGfVnxCbesFaMBHvBaPPZbaZoZCGgrJgBdCqGrtGMdmtJBRwSTZvUmjFLOWhhkALLEbcAVxwFDJCkvxsUdaGwkCXhxIFhaAcDffAmYLJsBlXCDFxDBUeGxTyRLSNeJclZUONvaFbSnMvYbKbrWTKmERYSivGoFwspIsjBHHksbIYLNGQRPxdVwzrkbLUMWjbXGolXMKUFZmHButvJZOlduxlraoRxydpOmgLKWtmplljItNNxzGzqbHhTXyPAiNCGpJKgLkKDJVPdkXaISEZGmkLSNSnOEKNXLRFpCHWQvbCGzuYLDPJnQymlVKfYUykucojsgSyckydidGSdjnXiioXGFseUPzTJkVuVyXBeYygarJUIitpJEYuBXxtGnMwZHWsCiPjDdHnMMvtgVjjpXgCoLWJTMMAfwmnImAwSLLwVJzYOcIQTapuxziKoWPDDBmhSfYROFosGxmEtSSDUYETwUMcnZLCAvqrMBWZootAkbSAeRrRrxUXkuegVdvlJjGfUupDNTqKSWmpKkHmQBIvRFCmvLlsSuRmYTenQosDYhPdjxLyKmtIBbiKuuTalIxoCpdHlhsavlRDXYsxBlUArwPsGPJGsEnEwYspAhwZmyKXUHXIlzKgLiCtDtbCNuHnCzveRJoswWzrUHvNnLJSwIRyVENfJNBMzdRoRLmSMkDqfseqTadFbYYFnnElrTjBYlJVHlwcSsrOYMpmXdyLMVtUpLzMzzqtUzEcsZsUPPUJeBBCdVXzyIGJXDxaXaFEsLuKPSOnLcKHucteEGutYsqhsgwQisIiKeSRfwjVtZYxPbdqxzttnMFRnheiMvqModwLIkpVEzzVPbADRgTfZXNpCGoorMwZikiQfKXGkdbOSOtZAwjrskEspBgeXRLniFEDOWoNlqqOZyrpQovlxaNFDBCJsjrysxMRfeEJMrJRkcGqjfSUUDLKnwcadJlsoPBEUsDJIOhrEMggHREPAOWrePhwEgxlvxHgQrCVoGXXwdESsBUSWTSkqwkcRKyFQvmbqAUjLaFsELMEVPNbRciUcSueLILHIJQHlWrvqPnPledJNVCmwTHfBToeFnaFndWrCXfKpuTjMAwgQWhMVmamBcETQBgLHAylOrZrfDbAFxzxkkAebQqnaLiOVJxdZtrzSxPZfYYBpYHxpbaHGVqSgPPhTDqMCbiMTKLFUWGpuYUhGTOtbiltQEjwuWKfXhiRdRZutLfesRuqhHTEzLTiugoFbxTgFfoTGLoHiJquJvFFXDDLYwIPjGQSZmcaVECduqvVCkdWXNTOoLOcHPmTavmeLldTbjIUXYAUTmMwpyqeVblDYaYWpdwuNhJrgDYQiYuZnyYfkvplFbnDkunVuFSrbXKxxMAkpxbxqJipPrgPxUTCjyNwpjezruOnKlSmFMlFbUIzMypluiLMiZYNuyVTzJRTZHyBYHwGNJzBaNhyDjLBLyRpVhNRPBbUcHJjhcoxzmrglayUlpeUaarBjKogpNskrcsRKqRUdozlCliXucWeJDFkoMNrDKpGQFyzdkiIxKeOyVoNYdwknviWLgPilaqGtsbLccKqIVuNUmhvKTZGjqDdoocqcexxSpbZJrGvXmmmmMrzmKgGQBNBSiuAUneqJgNvsblzuhMDhTGzpIDksJPLvTMMhSWIYZdNxDqAvrldBzTbsHEYFxSDWURsSADQdqsplnbmgTtJfMMpCQQMCyGPMdWwpLjnBeedyjcdDOZWLODtzTyrbRbXwPZOplZtexKmTeavTycDOEOUorwnaLfloSzNxqRZhDkpldvihtPnFcVEvObIOvXPSTUJTHewYEaXiYgNlXilgImichPahKESYveAZRxDUCtiMyStQeaoRMJevbVVzWzHSBZrYsvlocgKuAgCPZblpGTyVGmPvJjAaszosjgRwGmdUFLqOPzkzuXymWXAtKfbYJRWTfiyVaKrbjrVWPtsNlJiHepLJmskGMkXInnCHifEHjcnDJNjTjJefQZbmDcAECUoNFbtBdJluZFUBvGrzOYgJiCpUIAHzgAEtojIbqBRSvGDudQIuJnjokzYRTWvinLKHNgnxTfkKgIxBqdoAsgGCuGeknbMRqvJJCQOicQslJIuEruGNxdegjHRLJdoHfxcTeduKJuFoHDWrOxpYinwaOwyJmJPcbRVIGCiKQGegHKZzVHHCpYDfuAFPzvfyZxodikbbkLaDaAkkHUIvokQzqJltIcguObiltOTbMvjlnozYzMSoYtjFSjICmKGyGNplVHLLCtepjbXsTVKMDCxfInKZoYKyfSTFrvGbWnyyWOBnAiKeOZWHMgykQUVWyxOLfKijidYxHmPnPQjiQQLteUwTPqOSJwcEWQKiYTuERlsfapHJPVXdLVZUufNUDbGQwnZgmKxhoUMuhzRmDAQlDqRtTOdgAbomwfFiBwCoIMpdLUhVHucAEjhBmResdYCsptHJpJyrZcCilZvsWjfBFNVSDxrtgRmTAOKaFkAqYpAGKyezofzEZbwdgZndnkKfBnwbvPBaKCvOVbPGDDnkvARJJtqJrVMoUbCWNPIOYuKCihfYqXYyZHpWJErcDqrEhEpkfaqrMPOxmjAVWIQnoNXLdcGSJLehlPvmKBHGisEkigSXVZigxZZSPLdzzsBOoeULKPfLVWDGixOrIwfoYFNWetqcEYswPycRSOCzxzHPVREKSLTkSbJHyYCUqepAIDdCdMGukXINiDAdLtYYGKjFxVHEoiEVPsmsnZjAYIMEZKmjBxNSEGdWsnNNgoRKUHAYZiAnnNZMxEcrRlMdyfsCKppLNROmRCqlaxvbHBsGGiWxstfFGCgcRPNumnByFUdsirIgJiEXmPSIQuWYyjqselIqsingwPmazhRkPagxTdzVewNOMKvUlKdHwyWzCzSInMLhuWRGLrPTgtItOqSSaAuNLOhdgMdFeBPciyVzYTHtUXtwZwmVGFNWuIUjjXOJgmCDtLoZTrxEixDwAgutkNkuweHptnbpzPeMUgymRoTNzFYFAazauukrinTphAPcHSDiGHHMeahHuYkwFhDYJQxluoTPHPxYZrHvicOnRUBgejGsxsVTwPGBrCSeeiBzfPtvukyLWNxdNvZEmrDuGwemTXxhrJHpbqDYFWzSjOWpHxTeCVMrCFLquQBUsqBoRfCaDtGXcKrXUmttnGaSrbEQGQghioHauENjmDGSUTKylhrcWCQiaGocLLKphAmpOrKiZeAuQsRqkcDNYEyogAlJMIQbnFoRTRUQViyseoUuQvjttEFyljDOodihensleMhcQwlzfWrbhbwhqRhrsLArDSdgOjpBBmhwSuikYtPvFdawmiQmtecXdyFMmHIKXDrXtNuDnuqzPpTrImGIxTkdgsHxXgBYQkBRDqZHtiklgeAPZaMlBxKhAixLzqKBnKgRuafUAnFvstEUhxlUIdZhCOHYfKbCoxUaWpZVTfMQcXkfNPbqwqoLdTzfdhHhBhkPAcKfVyLkzKXjRJTUnJHrmpyXMRsKYpokmZzmRIKzDquVtNNilNZaQARKpGYJdfYlwTqzXdrFInQsPQVNcUuZBwQqtirZLHqDcBZfljwPTPWgKmOaZsJGtDQLoIytEMaOrwGDDSotRwApvhrvVkEoXphHTBEJcdZozToGYUNzpyuJocIZvygtAjwINNBrEuOBWuNjlEhyWhntFQFzDthwCfCKpRlpPDnaPuoKKfbyRrIPYKEaFnLZmFBmppPXBgwpyAxwnWWFKPLRMDowpQuTweqAYMnqZPLyJJpsIWnGjTBbzVewlEGtIiwRoEFsYDJdkatlUqlUldWkypHAjcDGOBylHQaSCmmGXrVuIsBtfkTHZdSXfiOQEGzUZPqxnbwoZXbAeROOehRXKgwkWUqKuACkaNlwbwESOoyCyTpWKigAInnaUfXvHERtfFrtftKenryCSCuVuIbWjKnMWVLzptodNrpGtjmOjKeJyLRxQbEEQZcPcUxKjfNPbsCxNDhpCljcIeOEQreSeFQBFflliXRCWtbQTaxuYbiYYYAdicUhucBLRMPhGZXHoaDdpZmQulubBhLaPkZxuWylSYomUZOngPpyYQfkvqmLPpbJYvvlkroVScXkiBezGuGPvlFXbknKSxAXhiFhKacnxICGhIpLLasBQHXSNKkSwwBbGAFetgMTxAuAqwnDUVsn'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'htmlpart': 'phdolIXPdTsHKfdoadpPfWXBkiSDWKGORPaHYlwvkuYHjPyeJDoaTswKpHSNqMMDQwHkEuCfKGqBZhZmjVEflKLRCwWcOErRISwyScnrhOAMoEjQsdbiNWqIZRwlxEqWvzxUugJJqTImGxsfysJcDGEnCamwkbyILnBChhsTFzvgUEKhiKPHdVNdjysJYLbgCIHCagKyfuXswFzmJHOwrEtMwIYqCnOteWBRwefYICdGbIWhlxzMwlIWGpMWgRZWzpoaqMQvTQDNJqTvkjxaUMIQbdmKDPjbZoFmaIjbDyDTwCkGCLzROyMHXdAqSRtBttUCvJtuyxvjlBXJdMzUDBtIPDjadBrqLDbKDdeFznFafjUhioHhcGgkdfIpoPGxWjrcZdWjJeQcRDwhXtekbNzFQbTtFJStNBXuVyZfKYYARtSiSMtLPEfqSOBrpyJlotaAcVutGgVhrVeVOaTBidaXwDjRUnfNOVgGiCkycpWsSCSCfozOwEiTunVdfPElCFyZXuOIRKFvEiTyuPExUcDVTNFsLvYmlOUqTvlMaWnXNpLQGpOTHSGxFPqlqsCeslnOKxvaXDKnQYufXatLmqFLygOsfbUsbbUWPEqyjUrtaEfXpxDwljeSYOTsgJllZlfWRjqtOKGwpKpyKewHNUWyJestNIbsWSvVQXMETeDacivvIbuqtIZbBXSQkYJNjmmYqnJWRXtLyqDKkzGegfHXWmIVfuXhHCqzfNfXNsRpZNeXhdEQqlcromCrPmYKkOQvrqqpXxaNDEoAkMKSVOHPcQEMVKjXQhMJGfVnxCbesFaMBHvBaPPZbaZoZCGgrJgBdCqGrtGMdmtJBRwSTZvUmjFLOWhhkALLEbcAVxwFDJCkvxsUdaGwkCXhxIFhaAcDffAmYLJsBlXCDFxDBUeGxTyRLSNeJclZUONvaFbSnMvYbKbrWTKmERYSivGoFwspIsjBHHksbIYLNGQRPxdVwzrkbLUMWjbXGolXMKUFZmHButvJZOlduxlraoRxydpOmgLKWtmplljItNNxzGzqbHhTXyPAiNCGpJKgLkKDJVPdkXaISEZGmkLSNSnOEKNXLRFpCHWQvbCGzuYLDPJnQymlVKfYUykucojsgSyckydidGSdjnXiioXGFseUPzTJkVuVyXBeYygarJUIitpJEYuBXxtGnMwZHWsCiPjDdHnMMvtgVjjpXgCoLWJTMMAfwmnImAwSLLwVJzYOcIQTapuxziKoWPDDBmhSfYROFosGxmEtSSDUYETwUMcnZLCAvqrMBWZootAkbSAeRrRrxUXkuegVdvlJjGfUupDNTqKSWmpKkHmQBIvRFCmvLlsSuRmYTenQosDYhPdjxLyKmtIBbiKuuTalIxoCpdHlhsavlRDXYsxBlUArwPsGPJGsEnEwYspAhwZmyKXUHXIlzKgLiCtDtbCNuHnCzveRJoswWzrUHvNnLJSwIRyVENfJNBMzdRoRLmSMkDqfseqTadFbYYFnnElrTjBYlJVHlwcSsrOYMpmXdyLMVtUpLzMzzqtUzEcsZsUPPUJeBBCdVXzyIGJXDxaXaFEsLuKPSOnLcKHucteEGutYsqhsgwQisIiKeSRfwjVtZYxPbdqxzttnMFRnheiMvqModwLIkpVEzzVPbADRgTfZXNpCGoorMwZikiQfKXGkdbOSOtZAwjrskEspBgeXRLniFEDOWoNlqqOZyrpQovlxaNFDBCJsjrysxMRfeEJMrJRkcGqjfSUUDLKnwcadJlsoPBEUsDJIOhrEMggHREPAOWrePhwEgxlvxHgQrCVoGXXwdESsBUSWTSkqwkcRKyFQvmbqAUjLaFsELMEVPNbRciUcSueLILHIJQHlWrvqPnPledJNVCmwTHfBToeFnaFndWrCXfKpuTjMAwgQWhMVmamBcETQBgLHAylOrZrfDbAFxzxkkAebQqnaLiOVJxdZtrzSxPZfYYBpYHxpbaHGVqSgPPhTDqMCbiMTKLFUWGpuYUhGTOtbiltQEjwuWKfXhiRdRZutLfesRuqhHTEzLTiugoFbxTgFfoTGLoHiJquJvFFXDDLYwIPjGQSZmcaVECduqvVCkdWXNTOoLOcHPmTavmeLldTbjIUXYAUTmMwpyqeVblDYaYWpdwuNhJrgDYQiYuZnyYfkvplFbnDkunVuFSrbXKxxMAkpxbxqJipPrgPxUTCjyNwpjezruOnKlSmFMlFbUIzMypluiLMiZYNuyVTzJRTZHyBYHwGNJzBaNhyDjLBLyRpVhNRPBbUcHJjhcoxzmrglayUlpeUaarBjKogpNskrcsRKqRUdozlCliXucWeJDFkoMNrDKpGQFyzdkiIxKeOyVoNYdwknviWLgPilaqGtsbLccKqIVuNUmhvKTZGjqDdoocqcexxSpbZJrGvXmmmmMrzmKgGQBNBSiuAUneqJgNvsblzuhMDhTGzpIDksJPLvTMMhSWIYZdNxDqAvrldBzTbsHEYFxSDWURsSADQdqsplnbmgTtJfMMpCQQMCyGPMdWwpLjnBeedyjcdDOZWLODtzTyrbRbXwPZOplZtexKmTeavTycDOEOUorwnaLfloSzNxqRZhDkpldvihtPnFcVEvObIOvXPSTUJTHewYEaXiYgNlXilgImichPahKESYveAZRxDUCtiMyStQeaoRMJevbVVzWzHSBZrYsvlocgKuAgCPZblpGTyVGmPvJjAaszosjgRwGmdUFLqOPzkzuXymWXAtKfbYJRWTfiyVaKrbjrVWPtsNlJiHepLJmskGMkXInnCHifEHjcnDJNjTjJefQZbmDcAECUoNFbtBdJluZFUBvGrzOYgJiCpUIAHzgAEtojIbqBRSvGDudQIuJnjokzYRTWvinLKHNgnxTfkKgIxBqdoAsgGCuGeknbMRqvJJCQOicQslJIuEruGNxdegjHRLJdoHfxcTeduKJuFoHDWrOxpYinwaOwyJmJPcbRVIGCiKQGegHKZzVHHCpYDfuAFPzvfyZxodikbbkLaDaAkkHUIvokQzqJltIcguObiltOTbMvjlnozYzMSoYtjFSjICmKGyGNplVHLLCtepjbXsTVKMDCxfInKZoYKyfSTFrvGbWnyyWOBnAiKeOZWHMgykQUVWyxOLfKijidYxHmPnPQjiQQLteUwTPqOSJwcEWQKiYTuERlsfapHJPVXdLVZUufNUDbGQwnZgmKxhoUMuhzRmDAQlDqRtTOdgAbomwfFiBwCoIMpdLUhVHucAEjhBmResdYCsptHJpJyrZcCilZvsWjfBFNVSDxrtgRmTAOKaFkAqYpAGKyezofzEZbwdgZndnkKfBnwbvPBaKCvOVbPGDDnkvARJJtqJrVMoUbCWNPIOYuKCihfYqXYyZHpWJErcDqrEhEpkfaqrMPOxmjAVWIQnoNXLdcGSJLehlPvmKBHGisEkigSXVZigxZZSPLdzzsBOoeULKPfLVWDGixOrIwfoYFNWetqcEYswPycRSOCzxzHPVREKSLTkSbJHyYCUqepAIDdCdMGukXINiDAdLtYYGKjFxVHEoiEVPsmsnZjAYIMEZKmjBxNSEGdWsnNNgoRKUHAYZiAnnNZMxEcrRlMdyfsCKppLNROmRCqlaxvbHBsGGiWxstfFGCgcRPNumnByFUdsirIgJiEXmPSIQuWYyjqselIqsingwPmazhRkPagxTdzVewNOMKvUlKdHwyWzCzSInMLhuWRGLrPTgtItOqSSaAuNLOhdgMdFeBPciyVzYTHtUXtwZwmVGFNWuIUjjXOJgmCDtLoZTrxEixDwAgutkNkuweHptnbpzPeMUgymRoTNzFYFAazauukrinTphAPcHSDiGHHMeahHuYkwFhDYJQxluoTPHPxYZrHvicOnRUBgejGsxsVTwPGBrCSeeiBzfPtvukyLWNxdNvZEmrDuGwemTXxhrJHpbqDYFWzSjOWpHxTeCVMrCFLquQBUsqBoRfCaDtGXcKrXUmttnGaSrbEQGQghioHauENjmDGSUTKylhrcWCQiaGocLLKphAmpOrKiZeAuQsRqkcDNYEyogAlJMIQbnFoRTRUQViyseoUuQvjttEFyljD'
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_htmlpart_none(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'randomkey': 'astringvalue'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'randomkey': 'astringvalue'
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_reqparam_none(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
