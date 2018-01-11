# -------------------------------------------------------------------------
#   Copyright (c) 2015-2017 AT&T Intellectual Property
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# -------------------------------------------------------------------------
#

import psycopg2

from osdf.utils.programming_utils import MetaSingleton


class PostgresDB(metaclass=MetaSingleton):
    conn, cur = None, None

    def connect(self, host=None, db=None, user=None, passwd=None, port=5432):
        if self.conn is None:
            self.conn = psycopg2.connect(host=host, port=port, user=user, password=passwd, database=db)
            self.cur = self.conn.cursor()
        return self.conn, self.cur
