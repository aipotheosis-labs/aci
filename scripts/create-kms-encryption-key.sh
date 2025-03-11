#!/bin/bash

awslocal kms create-key --tags '[{"TagKey":"_custom_id_","TagValue":"00000000-0000-0000-0000-000000000001"}]'
