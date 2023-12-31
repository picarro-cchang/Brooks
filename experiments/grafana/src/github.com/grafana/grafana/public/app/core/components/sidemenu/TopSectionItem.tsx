import React, { FC } from 'react';
import SideMenuDropDown from './SideMenuDropDown';

export interface Props {
  link: any;
}

const TopSectionItem: FC<Props> = props => {
  const { link } = props;
  return (
    <div className="sidemenu-item dropdown">
      <a className="sidemenu-link" href={link.url} target={link.target}>
        <span className="icon-circle sidemenu-icon">
          <i className={link.icon} style={{ width: '50px', height: '50px', paddingTop: '5px' }} />
          {link.img && <img src={link.img} style={{ width: '60px', height: '60px' }} />}
        </span>
      </a>
      <SideMenuDropDown link={link} />
    </div>
  );
};

export default TopSectionItem;
