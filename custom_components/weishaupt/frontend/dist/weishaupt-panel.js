var Y=globalThis,G=Y.ShadowRoot&&(Y.ShadyCSS===void 0||Y.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,ae=Symbol(),De=new WeakMap,L=class{constructor(r,e,t){if(this._$cssResult$=!0,t!==ae)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=r,this.t=e}get styleSheet(){let r=this.o,e=this.t;if(G&&r===void 0){let t=e!==void 0&&e.length===1;t&&(r=De.get(e)),r===void 0&&((this.o=r=new CSSStyleSheet).replaceSync(this.cssText),t&&De.set(e,r))}return r}toString(){return this.cssText}},He=o=>new L(typeof o=="string"?o:o+"",void 0,ae),F=(o,...r)=>{let e=o.length===1?o[0]:r.reduce((t,s,n)=>t+(i=>{if(i._$cssResult$===!0)return i.cssText;if(typeof i=="number")return i;throw Error("Value passed to 'css' function must be a 'css' function result: "+i+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+o[n+1],o[0]);return new L(e,o,ae)},Oe=(o,r)=>{if(G)o.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of r){let t=document.createElement("style"),s=Y.litNonce;s!==void 0&&t.setAttribute("nonce",s),t.textContent=e.cssText,o.appendChild(t)}},le=G?o=>o:o=>o instanceof CSSStyleSheet?(r=>{let e="";for(let t of r.cssRules)e+=t.cssText;return He(e)})(o):o;var{is:kt,defineProperty:Rt,getOwnPropertyDescriptor:Et,getOwnPropertyNames:St,getOwnPropertySymbols:At,getPrototypeOf:Tt}=Object,Q=globalThis,Ne=Q.trustedTypes,Ct=Ne?Ne.emptyScript:"",Mt=Q.reactiveElementPolyfillSupport,z=(o,r)=>o,de={toAttribute(o,r){switch(r){case Boolean:o=o?Ct:null;break;case Object:case Array:o=o==null?o:JSON.stringify(o)}return o},fromAttribute(o,r){let e=o;switch(r){case Boolean:e=o!==null;break;case Number:e=o===null?null:Number(o);break;case Object:case Array:try{e=JSON.parse(o)}catch{e=null}}return e}},Fe=(o,r)=>!kt(o,r),Le={attribute:!0,type:String,converter:de,reflect:!1,useDefault:!1,hasChanged:Fe};Symbol.metadata??=Symbol("metadata"),Q.litPropertyMetadata??=new WeakMap;var R=class extends HTMLElement{static addInitializer(r){this._$Ei(),(this.l??=[]).push(r)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(r,e=Le){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(r)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(r,e),!e.noAccessor){let t=Symbol(),s=this.getPropertyDescriptor(r,t,e);s!==void 0&&Rt(this.prototype,r,s)}}static getPropertyDescriptor(r,e,t){let{get:s,set:n}=Et(this.prototype,r)??{get(){return this[e]},set(i){this[e]=i}};return{get:s,set(i){let l=s?.call(this);n?.call(this,i),this.requestUpdate(r,l,t)},configurable:!0,enumerable:!0}}static getPropertyOptions(r){return this.elementProperties.get(r)??Le}static _$Ei(){if(this.hasOwnProperty(z("elementProperties")))return;let r=Tt(this);r.finalize(),r.l!==void 0&&(this.l=[...r.l]),this.elementProperties=new Map(r.elementProperties)}static finalize(){if(this.hasOwnProperty(z("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(z("properties"))){let e=this.properties,t=[...St(e),...At(e)];for(let s of t)this.createProperty(s,e[s])}let r=this[Symbol.metadata];if(r!==null){let e=litPropertyMetadata.get(r);if(e!==void 0)for(let[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let s=this._$Eu(e,t);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(r){let e=[];if(Array.isArray(r)){let t=new Set(r.flat(1/0).reverse());for(let s of t)e.unshift(le(s))}else r!==void 0&&e.push(le(r));return e}static _$Eu(r,e){let t=e.attribute;return t===!1?void 0:typeof t=="string"?t:typeof r=="string"?r.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(r=>this.enableUpdating=r),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(r=>r(this))}addController(r){(this._$EO??=new Set).add(r),this.renderRoot!==void 0&&this.isConnected&&r.hostConnected?.()}removeController(r){this._$EO?.delete(r)}_$E_(){let r=new Map,e=this.constructor.elementProperties;for(let t of e.keys())this.hasOwnProperty(t)&&(r.set(t,this[t]),delete this[t]);r.size>0&&(this._$Ep=r)}createRenderRoot(){let r=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Oe(r,this.constructor.elementStyles),r}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(r=>r.hostConnected?.())}enableUpdating(r){}disconnectedCallback(){this._$EO?.forEach(r=>r.hostDisconnected?.())}attributeChangedCallback(r,e,t){this._$AK(r,t)}_$ET(r,e){let t=this.constructor.elementProperties.get(r),s=this.constructor._$Eu(r,t);if(s!==void 0&&t.reflect===!0){let n=(t.converter?.toAttribute!==void 0?t.converter:de).toAttribute(e,t.type);this._$Em=r,n==null?this.removeAttribute(s):this.setAttribute(s,n),this._$Em=null}}_$AK(r,e){let t=this.constructor,s=t._$Eh.get(r);if(s!==void 0&&this._$Em!==s){let n=t.getPropertyOptions(s),i=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:de;this._$Em=s;let l=i.fromAttribute(e,n.type);this[s]=l??this._$Ej?.get(s)??l,this._$Em=null}}requestUpdate(r,e,t,s=!1,n){if(r!==void 0){let i=this.constructor;if(s===!1&&(n=this[r]),t??=i.getPropertyOptions(r),!((t.hasChanged??Fe)(n,e)||t.useDefault&&t.reflect&&n===this._$Ej?.get(r)&&!this.hasAttribute(i._$Eu(r,t))))return;this.C(r,e,t)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(r,e,{useDefault:t,reflect:s,wrapped:n},i){t&&!(this._$Ej??=new Map).has(r)&&(this._$Ej.set(r,i??e??this[r]),n!==!0||i!==void 0)||(this._$AL.has(r)||(this.hasUpdated||t||(e=void 0),this._$AL.set(r,e)),s===!0&&this._$Em!==r&&(this._$Eq??=new Set).add(r))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let r=this.scheduleUpdate();return r!=null&&await r,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,n]of this._$Ep)this[s]=n;this._$Ep=void 0}let t=this.constructor.elementProperties;if(t.size>0)for(let[s,n]of t){let{wrapped:i}=n,l=this[s];i!==!0||this._$AL.has(s)||l===void 0||this.C(s,void 0,n,l)}}let r=!1,e=this._$AL;try{r=this.shouldUpdate(e),r?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(t){throw r=!1,this._$EM(),t}r&&this._$AE(e)}willUpdate(r){}_$AE(r){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(r)),this.updated(r)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(r){return!0}update(r){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(r){}firstUpdated(r){}};R.elementStyles=[],R.shadowRootOptions={mode:"open"},R[z("elementProperties")]=new Map,R[z("finalized")]=new Map,Mt?.({ReactiveElement:R}),(Q.reactiveElementVersions??=[]).push("2.1.2");var ge=globalThis,ze=o=>o,ee=ge.trustedTypes,Ue=ee?ee.createPolicy("lit-html",{createHTML:o=>o}):void 0,Je="$lit$",S=`lit$${Math.random().toFixed(9).slice(2)}$`,Xe="?"+S,Pt=`<${Xe}>`,P=document,W=()=>P.createComment(""),I=o=>o===null||typeof o!="object"&&typeof o!="function",me=Array.isArray,jt=o=>me(o)||typeof o?.[Symbol.iterator]=="function",ce=`[ 	
\f\r]`,U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,We=/-->/g,Ie=/>/g,C=RegExp(`>|${ce}(?:([^\\s"'>=/]+)(${ce}*=${ce}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Be=/'/g,Ve=/"/g,Ze=/^(?:script|style|textarea|title)$/i,be=o=>(r,...e)=>({_$litType$:o,strings:r,values:e}),d=be(1),Wt=be(2),It=be(3),j=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),Ke=new WeakMap,M=P.createTreeWalker(P,129);function Ye(o,r){if(!me(o)||!o.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ue!==void 0?Ue.createHTML(r):r}var qt=(o,r)=>{let e=o.length-1,t=[],s,n=r===2?"<svg>":r===3?"<math>":"",i=U;for(let l=0;l<e;l++){let c=o[l],u,h,_=-1,g=0;for(;g<c.length&&(i.lastIndex=g,h=i.exec(c),h!==null);)g=i.lastIndex,i===U?h[1]==="!--"?i=We:h[1]!==void 0?i=Ie:h[2]!==void 0?(Ze.test(h[2])&&(s=RegExp("</"+h[2],"g")),i=C):h[3]!==void 0&&(i=C):i===C?h[0]===">"?(i=s??U,_=-1):h[1]===void 0?_=-2:(_=i.lastIndex-h[2].length,u=h[1],i=h[3]===void 0?C:h[3]==='"'?Ve:Be):i===Ve||i===Be?i=C:i===We||i===Ie?i=U:(i=C,s=void 0);let y=i===C&&o[l+1].startsWith("/>")?" ":"";n+=i===U?c+Pt:_>=0?(t.push(u),c.slice(0,_)+Je+c.slice(_)+S+y):c+S+(_===-2?l:y)}return[Ye(o,n+(o[e]||"<?>")+(r===2?"</svg>":r===3?"</math>":"")),t]},B=class o{constructor({strings:r,_$litType$:e},t){let s;this.parts=[];let n=0,i=0,l=r.length-1,c=this.parts,[u,h]=qt(r,e);if(this.el=o.createElement(u,t),M.currentNode=this.el.content,e===2||e===3){let _=this.el.content.firstChild;_.replaceWith(..._.childNodes)}for(;(s=M.nextNode())!==null&&c.length<l;){if(s.nodeType===1){if(s.hasAttributes())for(let _ of s.getAttributeNames())if(_.endsWith(Je)){let g=h[i++],y=s.getAttribute(_).split(S),v=/([.?@])?(.*)/.exec(g);c.push({type:1,index:n,name:v[2],strings:y,ctor:v[1]==="."?pe:v[1]==="?"?he:v[1]==="@"?_e:H}),s.removeAttribute(_)}else _.startsWith(S)&&(c.push({type:6,index:n}),s.removeAttribute(_));if(Ze.test(s.tagName)){let _=s.textContent.split(S),g=_.length-1;if(g>0){s.textContent=ee?ee.emptyScript:"";for(let y=0;y<g;y++)s.append(_[y],W()),M.nextNode(),c.push({type:2,index:++n});s.append(_[g],W())}}}else if(s.nodeType===8)if(s.data===Xe)c.push({type:2,index:n});else{let _=-1;for(;(_=s.data.indexOf(S,_+1))!==-1;)c.push({type:7,index:n}),_+=S.length-1}n++}}static createElement(r,e){let t=P.createElement("template");return t.innerHTML=r,t}};function D(o,r,e=o,t){if(r===j)return r;let s=t!==void 0?e._$Co?.[t]:e._$Cl,n=I(r)?void 0:r._$litDirective$;return s?.constructor!==n&&(s?._$AO?.(!1),n===void 0?s=void 0:(s=new n(o),s._$AT(o,e,t)),t!==void 0?(e._$Co??=[])[t]=s:e._$Cl=s),s!==void 0&&(r=D(o,s._$AS(o,r.values),s,t)),r}var ue=class{constructor(r,e){this._$AV=[],this._$AN=void 0,this._$AD=r,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(r){let{el:{content:e},parts:t}=this._$AD,s=(r?.creationScope??P).importNode(e,!0);M.currentNode=s;let n=M.nextNode(),i=0,l=0,c=t[0];for(;c!==void 0;){if(i===c.index){let u;c.type===2?u=new V(n,n.nextSibling,this,r):c.type===1?u=new c.ctor(n,c.name,c.strings,this,r):c.type===6&&(u=new fe(n,this,r)),this._$AV.push(u),c=t[++l]}i!==c?.index&&(n=M.nextNode(),i++)}return M.currentNode=P,s}p(r){let e=0;for(let t of this._$AV)t!==void 0&&(t.strings!==void 0?(t._$AI(r,t,e),e+=t.strings.length-2):t._$AI(r[e])),e++}},V=class o{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(r,e,t,s){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=r,this._$AB=e,this._$AM=t,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let r=this._$AA.parentNode,e=this._$AM;return e!==void 0&&r?.nodeType===11&&(r=e.parentNode),r}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(r,e=this){r=D(this,r,e),I(r)?r===p||r==null||r===""?(this._$AH!==p&&this._$AR(),this._$AH=p):r!==this._$AH&&r!==j&&this._(r):r._$litType$!==void 0?this.$(r):r.nodeType!==void 0?this.T(r):jt(r)?this.k(r):this._(r)}O(r){return this._$AA.parentNode.insertBefore(r,this._$AB)}T(r){this._$AH!==r&&(this._$AR(),this._$AH=this.O(r))}_(r){this._$AH!==p&&I(this._$AH)?this._$AA.nextSibling.data=r:this.T(P.createTextNode(r)),this._$AH=r}$(r){let{values:e,_$litType$:t}=r,s=typeof t=="number"?this._$AC(r):(t.el===void 0&&(t.el=B.createElement(Ye(t.h,t.h[0]),this.options)),t);if(this._$AH?._$AD===s)this._$AH.p(e);else{let n=new ue(s,this),i=n.u(this.options);n.p(e),this.T(i),this._$AH=n}}_$AC(r){let e=Ke.get(r.strings);return e===void 0&&Ke.set(r.strings,e=new B(r)),e}k(r){me(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,t,s=0;for(let n of r)s===e.length?e.push(t=new o(this.O(W()),this.O(W()),this,this.options)):t=e[s],t._$AI(n),s++;s<e.length&&(this._$AR(t&&t._$AB.nextSibling,s),e.length=s)}_$AR(r=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);r!==this._$AB;){let t=ze(r).nextSibling;ze(r).remove(),r=t}}setConnected(r){this._$AM===void 0&&(this._$Cv=r,this._$AP?.(r))}},H=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(r,e,t,s,n){this.type=1,this._$AH=p,this._$AN=void 0,this.element=r,this.name=e,this._$AM=s,this.options=n,t.length>2||t[0]!==""||t[1]!==""?(this._$AH=Array(t.length-1).fill(new String),this.strings=t):this._$AH=p}_$AI(r,e=this,t,s){let n=this.strings,i=!1;if(n===void 0)r=D(this,r,e,0),i=!I(r)||r!==this._$AH&&r!==j,i&&(this._$AH=r);else{let l=r,c,u;for(r=n[0],c=0;c<n.length-1;c++)u=D(this,l[t+c],e,c),u===j&&(u=this._$AH[c]),i||=!I(u)||u!==this._$AH[c],u===p?r=p:r!==p&&(r+=(u??"")+n[c+1]),this._$AH[c]=u}i&&!s&&this.j(r)}j(r){r===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,r??"")}},pe=class extends H{constructor(){super(...arguments),this.type=3}j(r){this.element[this.name]=r===p?void 0:r}},he=class extends H{constructor(){super(...arguments),this.type=4}j(r){this.element.toggleAttribute(this.name,!!r&&r!==p)}},_e=class extends H{constructor(r,e,t,s,n){super(r,e,t,s,n),this.type=5}_$AI(r,e=this){if((r=D(this,r,e,0)??p)===j)return;let t=this._$AH,s=r===p&&t!==p||r.capture!==t.capture||r.once!==t.once||r.passive!==t.passive,n=r!==p&&(t===p||s);s&&this.element.removeEventListener(this.name,this,t),n&&this.element.addEventListener(this.name,this,r),this._$AH=r}handleEvent(r){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,r):this._$AH.handleEvent(r)}},fe=class{constructor(r,e,t){this.element=r,this.type=6,this._$AN=void 0,this._$AM=e,this.options=t}get _$AU(){return this._$AM._$AU}_$AI(r){D(this,r)}};var Dt=ge.litHtmlPolyfillSupport;Dt?.(B,V),(ge.litHtmlVersions??=[]).push("3.3.3");var Ge=(o,r,e)=>{let t=e?.renderBefore??r,s=t._$litPart$;if(s===void 0){let n=e?.renderBefore??null;t._$litPart$=s=new V(r.insertBefore(W(),n),n,void 0,e??{})}return s._$AI(o),s};var ye=globalThis,x=class extends R{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let r=super.createRenderRoot();return this.renderOptions.renderBefore??=r.firstChild,r}update(r){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(r),this._$Do=Ge(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return j}};x._$litElement$=!0,x.finalized=!0,ye.litElementHydrateSupport?.({LitElement:x});var Ht=ye.litElementPolyfillSupport;Ht?.({LitElement:x});(ye.litElementVersions??=[]).push("4.2.2");var ke="-",we={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",mode_follow:"follows the running ebusd ({n} known)",mode_pinned:"pinned ({n} known)",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",write_hint:"Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",description:"Description",no_sensor:"no sensor",kept:"kept from before the reload, read again soon",through:"through {circuit}",read_now:"Read now",read_cost:"{n} requests to the bus, about {s} s, once",read_queued:"{n} requests queued; the grid fills in as they are answered",readable:"{usable} of {readable} readable messages loaded by ebusd as described",not_usable:"Messages not read",reason_write_only:"write only",reason_device_absent:"device not on the bus",absent_circuit:"{circuit}: {n} messages, device not on the bus",reason_mismatch:"not loaded as described",reason_other:"not read",disabled:"disabled",reloading:"The integration was reloaded: loading again\u2026",read_only_settings:"Settings left read-only",edit:"Change",write_now:"Write",cancel:"Cancel",confirm:"Write to the controller",confirm_clock:"Send the time",confirm_title:"Confirm: {setting} \u2014 {device}",current:"Current value",new_value:"New value",allowed:"Allowed",path:"Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",path_short:"bus address {address}, register {register}, from {source}",regulation_note:"This setting changes how the heating is regulated: it is written after your confirmation.",comfort_note:"Comfort setting: written at once and read back.",writing:"Writing\u2026",written_line:"{before} \u2192 {after}{frame}: {result}",not_written:"Not written: {message}",not_offered_writes_disabled:"writes are not enabled in the options",not_offered:"not offered on this installation: {reason}",switch_off_hint:"The writes switch is off: turn it on to write.",edit_days:"Edit",write_days:"Write the changed days",discard:"Discard changes",copy_to:"Copy to",copy:"Copy",cost:"{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",cost_one:"1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",interrupted:"no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",drag_hint:"Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",day_format:"use HH:MM-HH:MM, up to three ranges, or -",day_quarter:"times must be quarters of an hour, from 00:00 to 24:00",day_order:"a range must end after it starts",day_too_many:"at most three ranges",day_overlap:"ranges must not overlap",set_clock:"Set the clock",clock_confirm:"Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",clock_sent:"Sent {requested} ({frame}): {result}",clock_current:"Clock master now: {current}",col_device:"Device",col_menu:"Menu",col_label:"Setting",col_value:"Value",col_unit:"Unit",col_range:"Range (step) or choices",col_writable:"Writable",col_code:"Vendor code",col_scheme:"Code scheme",code:"Code",code_title:"{scheme}, document {document}",sort_by_code:"Sort by vendor code",report_codes:"Vendor codes: {schemes}.",report:"Printable report",export_csv:"Export CSV",report_title:"Settings of the installation",report_subtitle:"{date} \xB7 definitions {version} \xB7 read by the Weishaupt integration of Home Assistant",report_no_factory:"Factory values: the definitions do not carry them yet. An empty value was not read when the report was made.",report_blocked:"The browser blocked the report window: allow pop-ups for Home Assistant and try again.",faults:"Faults",fault_history:"Fault history",fault_counters:"Fault counters",fault_log:"Fault log of the system manager (selected entry)",fault_code:"Code",fault_text:"Text",fault_slot:"Slot",fault_values:"Values stored with it",fault_number:"Fault",fault_count:"Count",fault_none:"no fault stored",fault_unordered:"Order unknown: the pointer to the last entry is not read.",fault_no_time:"The boiler stores no time with an entry.",fault_log_fields:"Entry {id}: code {code}, type {type}, origin {device}, {time}",fault_log_hint:"The operating unit of the system manager selects the entry shown; selecting another one is a write, which the panel does not do.",faults_unread:"{n} of these messages are read by no enabled entity.",faults_read_once:"Read once on demand: not kept up to date unless their entities are enabled.",read_nothing:"Nothing to request: these messages are already read by enabled entities or waiting.",card_name:"Weishaupt weekly program",card_description:"The week grid of one weekly program of a Weishaupt controller.",card_no_entity:"Choose a program sensor of the Weishaupt integration in the card's settings.",card_missing:"{entity} does not exist, or is disabled: enable it in Settings \u2192 Entities (program sensors are created disabled).",card_unavailable:"{entity} is unavailable: ebusd or the controller does not answer.",card_unread:"not read yet",card_editor_entity:"Program sensor",card_editor_title:"Title (optional)",card_editor_today:"Mark today",card_editor_hint:"Program sensors are created disabled: a program not listed here is enabled in Settings \u2192 Entities.",card_edit:"Edit",card_edited_on:"Read from the store of {device}: change this program there.",edited_on_program:"Read from the store of {device}: change {program} of {device}; a change sent here would be acknowledged and lost.",edited_on_setting:"kept by {device}: changed there",stored_only_badge:"stored only",stored_only_note:"Stored in this device only: not followed by the installation (hot water follows the system manager).",card_type_hint:"Type up to three ranges a day, HH:MM-HH:MM, or - for none; only changed days are written.",card_edit_admin:"Days are changed by administrators, here or in the Weishaupt panel.",card_not_writable:"This program is not proven writable on its device: read only.",card_writing_day:"{day}: writing\u2026",card_written_day:"{day}: written and read back",card_failed_day:"{day}: not written: {message}",card_no_switch:"Writes are not enabled in the options of the integration.",read_queued_one:"1 request queued (about {s} s).",read_queued_n:"{n} requests queued (about {s} s).",read_after_first_pass:"They come after the first pass that follows a start: {n} reads still due, {wait}.",read_after_queue:"They come after {n} reads already due, {wait}.",about_s:"about {n} s",about_min:"about {n} min",read_scope_menu:"Read this menu once",read_scope_device:"Read this device once",read_scope_all:"Read everything once",read_scope_hint:"Rows no enabled entity follows are read once, at the pace of the bus, after what the entities wait for.",read_price_one:"1 request, {time}.",read_price_n:"{n} requests, {time}.",read_start:"Start",read_stop:"Stop",dismiss:"Close",job_running:"Reading: {done} of {total} asked, {read} with a value.",job_done:"Read once: {read} of {total} with a value. Not kept up to date: follow a row to keep it.",job_stopped:"Stopped: {done} of {total} asked, {stopped} withdrawn.",job_reload:"The integration reloaded: the reads not yet asked were dropped.",read_once:"read once",follow:"Follow",follow_all:"Follow all",follow_none:"Follow none",follow_blocked:"disabled by its device",follow_pending:"{n} changes to apply: {enable} to follow, {disable} to stop following.",follow_reload:"Home Assistant reloads the integration about {s} s after an entity is enabled: the panel reloads with it, and reads under way stop.",follow_defaults_off:"{n} of them are followed by default (live values, states, counters): disabled, they are no longer read, their history stops, and dashboards or automations that use them no longer find them.",follow_apply:"Apply",follow_discard:"Discard",follow_done:"{enabled} enabled, {disabled} disabled.",follow_reload_soon:"Home Assistant reloads the integration in about {s} s.",follow_refused:"{n} not changed: disabled by their device or config entry, or not this integration's.",writes_pill_on:"Writes: on ({n}/{max})",writes_pill_off:"Writes: locked",open_switch:"Open writes switch",items_count:"{n} items",items_count_one:"1 item",fault_hide_zero:"Hide zero counters ({n})",fault_all_zero:"All read counters are at 0.",copy_all:"every day",copy_weekdays:"Monday \u2013 Friday",copy_weekend:"Saturday, Sunday",search_placeholder:"Search settings, sensors, codes, keys\u2026",search_clear:"Clear",filter_all:"All",filter_writable:"Writable",filter_followed:"Followed",filter_unread:"Unread",search_results:"{n} matching rows",search_results_one:"1 matching row",search_empty:"No row matches this search.",bar_remove_hint:"{range} \u2014 click to remove",clear_day:"Clear",follow_details:"Show details ({n})"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",mode_follow:"suit l'ebusd en marche ({n} connus)",mode_pinned:"fix\xE9 ({n} connus)",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"lu par aucune entit\xE9 activ\xE9e : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir \xE0 jour",write_hint:"Modifiez un r\xE9glage avec son bouton Modifier (l'interrupteur d'\xE9criture doit \xEAtre allum\xE9). Confort : \xE9crit aussit\xF4t et relu ; r\xE9gulation : apr\xE8s une confirmation dans ce panneau. Ouvrir affiche l'entit\xE9.",description:"Description",no_sensor:"pas de sonde",kept:"conserv\xE9e d'avant le rechargement, relue bient\xF4t",through:"par {circuit}",read_now:"Lire maintenant",read_cost:"{n} requ\xEAtes sur le bus, environ {s} s, une seule fois",read_queued:"{n} requ\xEAtes en file ; la grille se remplit au fil des r\xE9ponses",readable:"{usable} sur {readable} messages lisibles charg\xE9s par ebusd comme d\xE9crits",not_usable:"Messages non lus",reason_write_only:"\xE9criture seule",reason_device_absent:"appareil absent du bus",absent_circuit:"{circuit} : {n} messages, appareil absent du bus",reason_mismatch:"non charg\xE9 comme d\xE9crit",reason_other:"non lu",disabled:"d\xE9sactiv\xE9e",reloading:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : nouveau chargement\u2026",read_only_settings:"R\xE9glages laiss\xE9s en lecture seule",edit:"Modifier",write_now:"\xC9crire",cancel:"Annuler",confirm:"\xC9crire dans le r\xE9gulateur",confirm_clock:"Envoyer l'heure",confirm_title:"Confirmer : {setting} \u2014 {device}",current:"Valeur actuelle",new_value:"Nouvelle valeur",allowed:"Valeurs autoris\xE9es",path:"\xC9crit \xE0 l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste apr\xE8s.",path_short:"adresse de bus {address}, registre {register}, depuis {source}",regulation_note:"Ce r\xE9glage modifie la r\xE9gulation du chauffage : il est \xE9crit apr\xE8s votre confirmation.",comfort_note:"R\xE9glage de confort : \xE9crit aussit\xF4t et relu.",writing:"\xC9criture\u2026",written_line:"{before} \u2192 {after}{frame} : {result}",not_written:"Non \xE9crit : {message}",not_offered_writes_disabled:"l'\xE9criture n'est pas activ\xE9e dans les options",not_offered:"non propos\xE9 sur cette installation : {reason}",switch_off_hint:"L'interrupteur d'\xE9criture est \xE9teint : allumez-le pour \xE9crire.",edit_days:"Modifier",write_days:"\xC9crire les jours modifi\xE9s",discard:"Abandonner les modifications",copy_to:"Copier vers",copy:"Copier",cost:"{days} jours modifi\xE9s : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",cost_one:"1 jour modifi\xE9 : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",interrupted:"pas de r\xE9ponse de Home Assistant (connexion interrompue) : l'\xE9criture a pu partir ou non ; v\xE9rifiez la valeur relue",drag_hint:"Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",day_format:"\xE9crivez HH:MM-HH:MM, trois plages au plus, ou -",day_quarter:"les heures doivent \xEAtre des quarts d'heure, de 00:00 \xE0 24:00",day_order:"une plage doit finir apr\xE8s son d\xE9but",day_too_many:"trois plages au plus",day_overlap:"les plages ne doivent pas se chevaucher",set_clock:"Mettre \xE0 l'heure",clock_confirm:"Enverra l'heure de Home Assistant \xE0 la seconde 00 de la minute suivante ({send_at}), \xE0 l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s apr\xE8s la seconde 00, rien n'est envoy\xE9.",clock_sent:"Envoy\xE9 {requested} ({frame}) : {result}",clock_current:"Horloge ma\xEEtresse maintenant : {current}",col_device:"Appareil",col_menu:"Menu",col_label:"R\xE9glage",col_value:"Valeur",col_unit:"Unit\xE9",col_range:"Plage (pas) ou choix",col_writable:"Inscriptible",col_code:"Code constructeur",col_scheme:"Num\xE9rotation du code",code:"Code",code_title:"{scheme}, document {document}",sort_by_code:"Trier par code constructeur",report_codes:"Codes constructeur : {schemes}.",report:"Rapport imprimable",export_csv:"Exporter en CSV",report_title:"R\xE9glages de l'installation",report_subtitle:"{date} \xB7 d\xE9finitions {version} \xB7 lus par l'int\xE9gration Weishaupt de Home Assistant",report_no_factory:"Valeurs d'usine : les d\xE9finitions ne les donnent pas encore. Une valeur vide n'\xE9tait pas lue au moment du rapport.",report_blocked:"Le navigateur a bloqu\xE9 la fen\xEAtre du rapport : autorisez les fen\xEAtres pour Home Assistant et r\xE9essayez.",faults:"D\xE9fauts",fault_history:"M\xE9moire de d\xE9fauts",fault_counters:"Compteurs de d\xE9fauts",fault_log:"Journal de d\xE9fauts du manager syst\xE8me (entr\xE9e s\xE9lectionn\xE9e)",fault_code:"Code",fault_text:"Texte",fault_slot:"Emplacement",fault_values:"Valeurs enregistr\xE9es avec lui",fault_number:"D\xE9faut",fault_count:"Nombre",fault_none:"aucun d\xE9faut enregistr\xE9",fault_unordered:"Ordre inconnu : le pointeur de la derni\xE8re entr\xE9e n'est pas lu.",fault_no_time:"La chaudi\xE8re n'enregistre pas d'heure avec une entr\xE9e.",fault_log_fields:"Entr\xE9e {id} : code {code}, type {type}, origine {device}, {time}",fault_log_hint:"Le tableau de commande du manager syst\xE8me choisit l'entr\xE9e affich\xE9e ; en choisir une autre est une \xE9criture, que le panneau ne fait pas.",faults_unread:"{n} de ces messages ne sont lus par aucune entit\xE9 activ\xE9e.",faults_read_once:"Lus une fois \xE0 la demande : pas tenus \xE0 jour tant que leurs entit\xE9s ne sont pas activ\xE9es.",read_nothing:"Rien \xE0 demander : ces messages sont d\xE9j\xE0 lus par des entit\xE9s activ\xE9es ou en attente.",card_name:"Programme hebdomadaire Weishaupt",card_description:"La grille de la semaine d'un programme hebdomadaire d'un r\xE9gulateur Weishaupt.",card_no_entity:"Choisissez un capteur de programme de l'int\xE9gration Weishaupt dans les r\xE9glages de la carte.",card_missing:"{entity} n'existe pas ou est d\xE9sactiv\xE9 : activez-le dans Param\xE8tres \u2192 Entit\xE9s (les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s).",card_unavailable:"{entity} est indisponible : ebusd ou le r\xE9gulateur ne r\xE9pond pas.",card_unread:"pas encore lu",card_editor_entity:"Capteur de programme",card_editor_title:"Titre (facultatif)",card_editor_today:"Marquer aujourd'hui",card_editor_hint:"Les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s : un programme absent de la liste s'active dans Param\xE8tres \u2192 Entit\xE9s.",card_edit:"Modifier",card_edited_on:"Lu dans la m\xE9moire de {device} : modifiez ce programme l\xE0-bas.",edited_on_program:"Lu dans la m\xE9moire de {device} : modifiez {program} de {device} ; une modification envoy\xE9e ici serait acquitt\xE9e puis perdue.",edited_on_setting:"tenu par {device} : \xE0 modifier l\xE0-bas",stored_only_badge:"m\xE9moris\xE9 uniquement",stored_only_note:"M\xE9moris\xE9 dans cet appareil uniquement : non suivi par l'installation (l'ECS suit le manager de cascade).",card_type_hint:"Saisissez jusqu'\xE0 trois plages par jour, HH:MM-HH:MM, ou - pour aucune ; seuls les jours modifi\xE9s sont \xE9crits.",card_edit_admin:"Les jours sont modifi\xE9s par les administrateurs, ici ou dans le panneau Weishaupt.",card_not_writable:"Ce programme n'est pas prouv\xE9 inscriptible sur son appareil : lecture seule.",card_writing_day:"{day} : \xE9criture\u2026",card_written_day:"{day} : \xE9crit et relu",card_failed_day:"{day} : non \xE9crit : {message}",card_no_switch:"L'\xE9criture n'est pas activ\xE9e dans les options de l'int\xE9gration.",read_queued_one:"1 requ\xEAte en file (environ {s} s).",read_queued_n:"{n} requ\xEAtes en file (environ {s} s).",read_after_first_pass:"Elles passent apr\xE8s la premi\xE8re lecture qui suit un d\xE9marrage : {n} lectures encore dues, {wait}.",read_after_queue:"Elles passent apr\xE8s {n} lectures d\xE9j\xE0 dues, {wait}.",about_s:"environ {n} s",about_min:"environ {n} min",read_scope_menu:"Lire ce menu une fois",read_scope_device:"Lire cet appareil une fois",read_scope_all:"Tout lire une fois",read_scope_hint:"Les lignes qu'aucune entit\xE9 activ\xE9e ne suit sont lues une fois, au rythme du bus, apr\xE8s ce qu'attendent les entit\xE9s.",read_price_one:"1 requ\xEAte, {time}.",read_price_n:"{n} requ\xEAtes, {time}.",read_start:"D\xE9marrer",read_stop:"Arr\xEAter",dismiss:"Fermer",job_running:"Lecture : {done} sur {total} demand\xE9es, {read} avec une valeur.",job_done:"Lu une fois : {read} sur {total} avec une valeur. Pas tenu \xE0 jour : suivez une ligne pour la garder \xE0 jour.",job_stopped:"Arr\xEAt\xE9 : {done} sur {total} demand\xE9es, {stopped} retir\xE9es.",job_reload:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : les lectures pas encore demand\xE9es ont \xE9t\xE9 abandonn\xE9es.",read_once:"lu une fois",follow:"Suivre",follow_all:"Tout suivre",follow_none:"Ne rien suivre",follow_blocked:"d\xE9sactiv\xE9e par son appareil",follow_pending:"{n} changements \xE0 appliquer : {enable} \xE0 suivre, {disable} \xE0 ne plus suivre.",follow_reload:"Home Assistant recharge l'int\xE9gration environ {s} s apr\xE8s l'activation d'une entit\xE9 : le panneau se recharge avec elle, et les lectures en cours s'arr\xEAtent.",follow_defaults_off:"{n} d'entre elles sont suivies par d\xE9faut (valeurs instantan\xE9es, \xE9tats, compteurs) : d\xE9sactiv\xE9es, elles ne sont plus lues, leur historique s'arr\xEAte, et les tableaux de bord ou automatisations qui les utilisent ne les trouvent plus.",follow_apply:"Appliquer",follow_discard:"Annuler",follow_done:"{enabled} activ\xE9es, {disabled} d\xE9sactiv\xE9es.",follow_reload_soon:"Home Assistant recharge l'int\xE9gration dans environ {s} s.",follow_refused:"{n} non modifi\xE9es : d\xE9sactiv\xE9es par leur appareil ou leur entr\xE9e, ou pas de cette int\xE9gration.",writes_pill_on:"\xC9critures : actives ({n}/{max})",writes_pill_off:"\xC9critures : verrouill\xE9es",open_switch:"Ouvrir l'interrupteur",items_count:"{n} \xE9l\xE9ments",items_count_one:"1 \xE9l\xE9ment",fault_hide_zero:"Masquer les compteurs \xE0 0 ({n})",fault_all_zero:"Tous les compteurs lus sont \xE0 0.",copy_all:"tous les jours",copy_weekdays:"lundi \u2013 vendredi",copy_weekend:"samedi, dimanche",search_placeholder:"Rechercher un r\xE9glage, une sonde, un code, une cl\xE9\u2026",search_clear:"Effacer",filter_all:"Tout",filter_writable:"Modifiables",filter_followed:"Suivis",filter_unread:"Non lus",search_results:"{n} lignes correspondantes",search_results_one:"1 ligne correspondante",search_empty:"Aucune ligne ne correspond \xE0 cette recherche.",bar_remove_hint:"{range} \u2014 cliquer pour retirer",clear_day:"Vider",follow_details:"Voir le d\xE9tail ({n})"}},T={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function rt(o){let r=(o??"en").split("-")[0];return r in we?r:"en"}function a(o,r,e={}){return(we[o]?.[r]??we.en[r]??r).replace(/\{(\w+)\}/g,(s,n)=>String(e[n]??`{${n}}`))}function f(o,r){return o?o[r]??o.en??Object.values(o)[0]??"":""}function Re(o,r,e){if(!r)return null;let t=r.values[o.index];if(t===void 0)return null;if(t===ke)return a(e,"not_available");if(o.absent!==null&&o.absent!==void 0&&Number(t)===o.absent)return a(e,"no_sensor");if(o.values){let s=o.values[t];return s?f(s,e):t}return o.unit?`${t} ${o.unit}`:t}function nt(o,r){let e=t=>t.split(" (")[0].trim().toLowerCase();return!o||e(o)===e(r)}function O(o,r){for(let e of o.messages??[o.message]){let t=r[e];if(t)return t}return null}function it(o,r){let e=new Map,t=[];for(let s of o)if(s.reason==="device_absent"){let n=s.key.split("/")[0];e.set(n,(e.get(n)??0)+1)}else t.push(`${s.key}: ${a(r,`reason_${s.reason}`)}`);for(let[s,n]of e)t.push(a(r,"absent_circuit",{circuit:s,n}));return t}function Ee(o,r){let e=r?.values[o.index];if(e===void 0||e===""||e===ke)return"";let t=o.writable?.options;if(t){let s=t.find(n=>n.name===e);return s?String(s.raw):""}return Number.isNaN(Number(e))?"":e}function Se(o){return o.read?!o.entity_id&&!o.passive?"not_listened":"waiting":"not_loaded"}function ot(o,r){let e=Math.max(0,Math.round(o));return e<90?a(r,"seconds_ago",{n:e}):e<90*60?a(r,"minutes_ago",{n:Math.round(e/60)}):e<36*3600?a(r,"hours_ago",{n:Math.round(e/3600)}):a(r,"days_ago",{n:Math.round(e/86400)})}function Qe(o,r){return new Intl.NumberFormat(r==="fr"?"fr-FR":"en-GB",{maximumFractionDigits:3,useGrouping:!1}).format(o).replace("-","\u2212")}function at(o,r,e){if(!o||o.min==null&&o.max==null)return"";let t=n=>n==null?"\u2026":Qe(n,e),s=`${t(o.min)} \u2026 ${t(o.max)}${r?` ${r}`:""}`;return o.step?`${s} (${Qe(o.step,e)})`:s}function Ae(o,r="en"){return o.values||o.writable?.options?"":at(o.range,o.unit,r)}var lt=3,ve=15;function N(o){let r=o.trim();if(r===""||r==="-")return{ranges:[]};let e=[];for(let t of r.split(",")){let s=/^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(t);if(!s)return{error:"day_format"};let[n,i,l,c]=s.slice(1).map(Number),u=n*60+i,h=l*60+c;if([i,c].some(_=>_%ve)||u>1440||h>1440||i>45||c>45)return{error:"day_quarter"};if(u>=h)return{error:"day_order"};e.push([u,h])}if(e.length>lt)return{error:"day_too_many"};e.sort((t,s)=>t[0]-s[0]);for(let t=1;t<e.length;t++)if(e[t][0]<e[t-1][1])return{error:"day_overlap"};return{ranges:e}}function q(o){let r=Math.floor(o/60),e=o%60;return`${String(r).padStart(2,"0")}:${String(e).padStart(2,"0")}`}function K(o){return o.length?o.map(([r,e])=>`${q(r)}-${q(e)}`).join(", "):"-"}function se(o,r){let e=n=>Math.round(Math.min(1,Math.max(0,n))*1440/ve)*ve,t=Math.min(e(o),e(r)),s=Math.max(e(o),e(r));return s===t&&(s=Math.min(1440,t+60)),[t,s]}function dt(o,r,e){let[t,s]=se(r,e),n=[];for(let[l,c]of o)l<=s&&c>=t?(t=Math.min(t,l),s=Math.max(s,c)):n.push([l,c]);let i=[...n,[t,s]].sort((l,c)=>l[0]-c[0]);return i.length>lt?null:i}function et(o){let[r,e]=o.split(":").map(t=>Number(t));return r*60+(e||0)}function ct(o){return o.map(([r,e])=>{let t=et(r),s=et(e);return{left:t/1440*100,width:Math.max(0,s-t)/1440*100,text:`${r}-${e}`}})}function J(o){let r=[],e=(t,s)=>{for(let n of o.filter(i=>i.parent===t))r.push([n,s]),e(n.id,s+1)};e("",0);for(let t of o)r.some(([s])=>s.id===t.id)||r.push([t,0]);return r}function Te(o,r,e){let t=[];for(let s of o.devices){let n=new Map(s.menus.map(u=>[u.id,u])),i=u=>{let h=[];for(let _=n.get(u);_;_=n.get(_.parent))h.unshift(f(_.label,e));return h.join(" \u203A ")},l=new Map(J(s.menus).map(([u],h)=>[u.id,h])),c=s.rows.filter(u=>u.kind==="setting").sort((u,h)=>(l.get(u.menu)??999)-(l.get(h.menu)??999));for(let u of c){let _=O(u,r)?.values[u.index],g;_===void 0?g=a(e,Se(u)):_===ke?g=a(e,"not_available"):g=u.values&&f(u.values[_],e)||_;let y=u.values||u.writable?.options,v=u.writable?.minimum!=null?{min:u.writable.minimum,max:u.writable.maximum,step:u.writable.step}:u.range,w=u.writable?.options?u.writable.options.map($=>f($.label,e)).join(", "):u.values?Object.values(u.values).map($=>f($,e)).join(", "):"";t.push({device:f(s.label,e),menu:i(u.menu),label:f(u.label,e),value:g,unit:u.values?"":u.unit??"",range:y?w:at(v,null,e),writable:u.writable?a(e,u.writable.risk):a(e,"read_only"),code:Pe(u),scheme:[...new Set((u.vendor_codes??[]).map($=>xe($,e)))].join(", ")})}}return t}var ut=["device","menu","label","value","unit","range","writable","code","scheme"],tt=["menu","label","code","value","unit","range","writable"];function Ot(o){return ut.map(r=>a(o,`col_${r}`))}function pt(o,r){let e=r==="fr"?";":",",t=n=>n.includes(e)||/["\n\r]/.test(n)?`"${n.replace(/"/g,'""')}"`:n;return"\uFEFF"+[Ot(r),...o.map(n=>ut.map(i=>n[i]))].map(n=>n.map(t).join(e)).join(`\r
`)+`\r
`}function A(o){return o.replace(/[&<>"']/g,r=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[r])}function ht(o,r,e){let t=[...new Set(o.map(i=>i.device))],s=tt.map(i=>a(r,`col_${i}`)),n=t.map(i=>{let l=o.filter(h=>h.device===i),c=[...new Set(l.flatMap(h=>h.scheme?h.scheme.split(", "):[]))],u=c.length?`<p>${A(a(r,"report_codes",{schemes:c.join(", ")}))}</p>`:"";return`<section><h2>${A(i)}</h2><table><thead><tr>${s.map(h=>`<th>${A(h)}</th>`).join("")}</tr></thead><tbody>${l.map(h=>`<tr>${tt.map(_=>`<td>${A(h[_])}</td>`).join("")}</tr>`).join("")}</tbody></table>${u}</section>`});return`<!doctype html><html lang="${r}"><head><meta charset="utf-8"><title>${A(e.title)}</title>
<style>
@page{size:A4;margin:15mm 12mm}
body{font:10pt system-ui,sans-serif;margin:16px;color:#000;background:#fff}
h1{font-size:15pt;margin:0 0 4px}h2{font-size:12pt;margin:16px 0 6px}p{margin:0 0 8px;color:#333}
table{border-collapse:collapse;width:100%;table-layout:auto}
th,td{border:1px solid #999;padding:4px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eee}thead{display:table-header-group}tfoot{display:table-footer-group}
tr,td,th{break-inside:avoid;page-break-inside:avoid}
@media print{body{margin:0}h2{break-after:avoid;page-break-after:avoid}th{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><h1>${A(e.title)}</h1><p>${A(e.subtitle)}</p>${n.join("")}
<p>${A(a(r,"report_no_factory"))}</p></body></html>`}function Ce(o,r){if(o.queued===0)return a(r,"read_nothing");let e=a(r,o.queued===1?"read_queued_one":"read_queued_n",{n:o.queued,s:o.seconds});if(o.ahead===0)return e;let t=o.wait>=90?Math.round(o.wait/60):0,s=t?a(r,"about_min",{n:t}):a(r,"about_s",{n:o.wait});return`${e} ${a(r,o.first_pass?"read_after_first_pass":"read_after_queue",{n:o.ahead,wait:s})}`}function _t(o){return(o.getDay()+6)%7+1}function st(o,r){return o>=90?a(r,"about_min",{n:Math.round(o/60)}):a(r,"about_s",{n:o})}function ft(o,r){if(o.queued===0)return a(r,"read_nothing");let e=a(r,o.queued===1?"read_price_one":"read_price_n",{n:o.queued,time:st(o.seconds,r)});return o.ahead===0?e:`${e} ${a(r,o.first_pass?"read_after_first_pass":"read_after_queue",{n:o.ahead,wait:st(o.wait,r)})}`}function gt(o,r){return o.stopped?a(r,"job_stopped",{done:o.done,total:o.total,stopped:o.stopped}):o.ended?a(r,"job_done",{read:o.read,total:o.total}):a(r,"job_running",{done:o.done,total:o.total,read:o.read})}function Me(o,r){let e=new Map(r.filter(i=>!!i&&!i.blocked).map(i=>[i.entity_id,i])),t=[],s=[],n=0;for(let[i,l]of Object.entries(o)){let c=e.get(i);!c||c.enabled===l||(l?t.push(i):(s.push(i),c.default&&(n+=1)))}return{enable:t.sort(),disable:s.sort(),defaultsOff:n}}function re(o,r,e){let t={...o};for(let s of r)!s||s.blocked||(s.enabled===e?delete t[s.entity_id]:t[s.entity_id]=e);return t}function te(o){return o.normalize("NFD").replace(/\p{Diacritic}/gu,"").toLowerCase()}function $e(o){return o.replace(/\s+/g,"").toLowerCase()}function Pe(o){return(o.vendor_codes??[]).map(r=>r.code).join(", ")}function xe(o,r){let e=f(o.scheme_label,r)||o.scheme;return o.document?a(r,"code_title",{scheme:e,document:o.document}):e}function mt(o,r){let e=o.vendor_codes??[],t=[...new Set(e.map(s=>xe(s,r)))];return t.length===1?t[0]:e.map(s=>`${s.code}: ${xe(s,r)}`).join(`
`)}function bt(o,r){if(!r)return o;let e=s=>$e(s.vendor_codes?.[0]?.code??""),t=r==="asc"?1:-1;return o.map((s,n)=>({row:s,i:n,k:e(s)})).sort((s,n)=>!s.k||!n.k?(s.k?0:1)-(n.k?0:1)||s.i-n.i:t*s.k.localeCompare(n.k,"en",{numeric:!0})||s.i-n.i).map(s=>s.row)}function yt(o,r,e,t,s){if(e==="writable"&&(!o.writable||o.edited_on)||e==="followed"&&!o.listened&&!o.follow?.enabled||e==="unread"&&O(o,t)!==null)return!1;let n=te(r).trim().split(/\s+/).filter(Boolean);if(!n.length)return!0;let i=$e(te(r));if((o.vendor_codes??[]).some(c=>$e(te(c.code)).includes(i)))return!0;let l=te([f(o.label,s),f(o.description,s),o.key,o.message,o.writable?.register??"",...(o.vendor_codes??[]).map(c=>c.code)].join(" "));return n.every(c=>l.includes(c))}var X=class extends x{constructor(){super(),this.language="en",this.unread="",this.today=0,this.now=-1,this.caption=""}render(){let r=this.language,e=T[r]??T.en,t=this.now>=0?this.now:(()=>{let n=new Date;return n.getHours()*60+n.getMinutes()})(),s=Math.min(100,Math.max(0,t/1440*100));return d`<table>
      ${this.caption?d`<caption class="visually-hidden">${this.caption}</caption>`:p}
      <thead>
        <tr>
          <th scope="col"><span class="visually-hidden">${a(r,"programs")}</span></th>
          <td class="scale" aria-hidden="true">
            ${[0,6,12,18,24].map(n=>d`<span style="left:${n/24*100}%">${n}</span>`)}
          </td>
        </tr>
      </thead>
      <tbody>
        ${e.map((n,i)=>{let l=this.days?.[String(i+1)],c=l==null?this.unread||a(r,"day_unread"):l.length?l.map(([u,h])=>`${u}-${h}`).join(", "):a(r,"day_none");return d`<tr class=${this.today===i+1?"today":""}>
            <th scope="row">${n}</th>
            <td>
              <div class="day" aria-hidden="true">
                ${(l??[]).length?ct(l).map(u=>d`<span class="bar" style="left:${u.left}%;width:${u.width}%"></span>`):p}
                ${this.today===i+1?d`<span class="now-line" style="left:${s}%"></span>`:p}
              </div>
              <div class="day-text">${c}</div>
            </td>
          </tr>`})}
      </tbody>
    </table>`}};X.properties={days:{attribute:!1},language:{type:String},unread:{type:String},today:{type:Number},now:{type:Number},caption:{type:String}},X.styles=F`
    :host {
      display: block;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    tbody th {
      font-weight: 400;
      width: 8em;
    }
    tr.today th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .scale span:first-child {
      transform: none;
    }
    .scale span:last-child {
      transform: translateX(-100%);
    }
    .day {
      position: relative;
      height: 14px;
      background-color: var(--secondary-background-color);
      background-image: linear-gradient(
        to right,
        transparent calc(25% - 0.5px),
        var(--divider-color) 25%,
        transparent calc(25% + 0.5px),
        transparent calc(50% - 0.5px),
        var(--divider-color) 50%,
        transparent calc(50% + 0.5px),
        transparent calc(75% - 0.5px),
        var(--divider-color) 75%,
        transparent calc(75% + 0.5px)
      );
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .now-line {
      position: absolute;
      top: -2px;
      bottom: -2px;
      width: 2px;
      margin-left: -1px;
      background: var(--error-color);
      border-radius: 1px;
      pointer-events: none;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
  `;customElements.get("weishaupt-week-grid")||customElements.define("weishaupt-week-grid",X);var Nt="__all__",ne="__definitions__",ie="__faults__";function wt(o,r,e){let t=o.find(s=>s.id===r)?.parent??"";for(;t;){if(t===e)return!0;t=o.find(s=>s.id===t)?.parent??""}return!1}var je="programs",Z=class extends x{constructor(){super();this._offset=0;this._readings={},this._programs={},this._available=!0,this._tick=0,this._queued={},this._reloading=!1,this._draft="",this._rowResult={},this._busy=!1,this._weekDraft={},this._weekResult={},this._reads={},this._pending={},this._hideZeroFaults=!0,this._query="",this._filter="all",this._codeSort="",this._dragError={}}get _lang(){return rt(this.hass?.language)}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>this._tick+=1,3e4),this._entryId&&this._subscribe(this._entryId)}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._timer),this._unsubscribe?.(),this._unsubscribe=void 0}willUpdate(e){e.has("hass")&&this.hass&&this._installations===void 0&&!this._loading&&(this._loading="installations",this.hass.callWS({type:"weishaupt/panel/installations"}).then(t=>{this._installations=t,t.length&&this._select(t[0].entry_id)}).catch(t=>this._error=t.message))}updated(e){e.has("_dialog")&&this._dialog?this.renderRoot.querySelector(".dialog button.cancel")?.focus():e.has("_editing")&&this._editing&&this.renderRoot.querySelector("form.edit input, form.edit select")?.focus()}async _select(e,t=!1){this._entryId=e,t||(this._tree=void 0,this._device=void 0,this._menu=void 0),this._readings={},this._programs={},this._queued={};try{let s=await this.hass.callWS({type:"weishaupt/panel/tree",entry_id:e});this._tree=s,this._loadFaults(0),s.devices.some(n=>n.id===this._device)||(this._device=s.devices[0]?.id,this._menu=s.devices[0]?.menus[0]?.id),await this._subscribe(e)}catch(s){if(t)throw s;this._error=s.message}}_loadFaults(e){window.clearTimeout(this._faultTimer),this._faultTimer=window.setTimeout(async()=>{if(this._entryId)try{this._faults=await this.hass.callWS({type:"weishaupt/panel/faults",entry_id:this._entryId})}catch{}},e)}async _readFaults(e){let t=await this.hass.callWS({type:"weishaupt/panel/read_faults",entry_id:this._entryId,device:e});this._queued={...this._queued,[`faults:${e}`]:t}}_report(){let e=this._tree,t=this._lang,s=Te(e,this._readings,t),n=new Date().toLocaleString(t==="fr"?"fr-FR":"en-GB"),i=ht(s,t,{title:a(t,"report_title"),subtitle:a(t,"report_subtitle",{date:n,version:e.definitions.version})}),l=window.open("","_blank");if(!l){this._rowResult={...this._rowResult,__report__:{text:a(t,"report_blocked"),error:!0}};return}l.document.open(),l.document.write(i),l.document.close(),l.focus(),l.print()}_csv(){let e=this._tree,t=this._lang,s=new Blob([pt(Te(e,this._readings,t),t)],{type:"text/csv;charset=utf-8"}),n=document.createElement("a");n.href=URL.createObjectURL(s),n.download=`weishaupt-settings-${new Date().toISOString().slice(0,10)}.csv`,n.click(),window.setTimeout(()=>URL.revokeObjectURL(n.href),1e3)}_faultsView(e){let t=this._lang,s=this._queued[`faults:${e.device}`],n=i=>i==null?"-":String(i);return d`<h2>${f(e.label,t)} — ${a(t,"faults")}</h2>
      ${e.not_listened?d`<p class="secondary">${a(t,"faults_unread",{n:e.not_listened})}</p>
            ${s!==void 0?d`<p class="secondary" role="status">${Ce(s,t)}</p>`:e.to_read===0||e.unread===0?d`<p class="secondary">${a(t,"faults_read_once")}</p>`:d`<p>
                    <button class="link" @click=${()=>this._readFaults(e.device)}>${a(t,"read_now")}</button>
                    <span class="secondary"
                      >${a(t,"read_cost",{n:e.to_read,s:Math.round(e.to_read*2.2)})}</span
                    >
                  </p>`}`:p}
      ${e.history?d`<h3>${a(t,"fault_history")}</h3>
            ${e.history.entries===null?d`<p class="secondary">${a(t,"day_unread")}</p>`:e.history.entries.length===0?d`<p class="secondary">${a(t,"fault_none")}</p>`:d`${e.history.ordered?p:d`<p class="secondary">${a(t,"fault_unordered")}</p>`}
                    <div class="scroll">
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">${a(t,"fault_code")}</th>
                            <th scope="col">${a(t,"fault_text")}</th>
                            <th scope="col">${a(t,"fault_values")}</th>
                            <th scope="col">${a(t,"fault_slot")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${e.history.entries.map(i=>d`<tr>
                              <th scope="row" class="nowrap">${i.code}</th>
                              <td>${f(i.text,t)||"-"}</td>
                              <td class="secondary">
                                ${i.values.map(l=>`${f(l.label,t)} ${l.value_labels?f(l.value_labels,t):l.value===null?"-":`${l.value}${l.unit?` ${l.unit}`:""}`}`).join(" \xB7 ")}
                              </td>
                              <td>${i.slot}</td>
                            </tr>`)}
                        </tbody>
                      </table>
                    </div>
                    <p class="secondary">${a(t,"fault_no_time")}</p>`}`:p}
      ${e.counters?(()=>{let i=e.counters.filter(c=>c.count===0).length,l=this._hideZeroFaults?e.counters.filter(c=>c.count!==0):e.counters;return d`<h3>${a(t,"fault_counters")}</h3>
              ${i>0?d`<label class="inline-check secondary">
                    <input
                      type="checkbox"
                      .checked=${this._hideZeroFaults}
                      @change=${c=>this._hideZeroFaults=c.target.checked}
                    />
                    ${a(t,"fault_hide_zero",{n:i})}
                  </label>`:p}
              ${l.length===0?d`<p class="secondary">${a(t,"fault_all_zero")}</p>`:d`<div class="scroll">
                    <table>
                      <thead>
                        <tr>
                          <th scope="col">${a(t,"fault_number")}</th>
                          <th scope="col">${a(t,"fault_count")}</th>
                          <th scope="col">${a(t,"fault_text")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${l.map(c=>d`<tr>
                            <th scope="row">${c.number}</th>
                            <td class=${c.count?"num":"secondary num"}>
                              ${c.count===null?a(t,"day_unread"):c.count}
                            </td>
                            <td>${f(c.text,t)||"-"}</td>
                          </tr>`)}
                      </tbody>
                    </table>
                  </div>`}`})():p}
      ${e.log?d`<h3>${a(t,"fault_log")}</h3>
            <p>
              ${e.log.entry?a(t,"fault_log_fields",{id:n(e.log.entry.id),code:n(e.log.entry.code),type:n(e.log.entry.type),device:n(e.log.entry.device),time:n(e.log.entry.time)}):a(t,"day_unread")}
            </p>
            <p class="secondary">${a(t,"fault_log_hint")}</p>`:p}`}async _readProgram(e){if(!this._entryId)return;let t=await this.hass.callWS({type:"weishaupt/panel/read_program",entry_id:this._entryId,program:e});this._queued={...this._queued,[e]:t}}async _subscribe(e){this._unsubscribe?.(),this._unsubscribe=await this.hass.connection.subscribeMessage(t=>this._live(t),{type:"weishaupt/panel/subscribe",entry_id:e})}_live(e){if(this._offset=Date.now()/1e3-e.now,e.reloaded){this._unsubscribe=void 0,this._reloading=!0,this._reads=Object.fromEntries(Object.entries(this._reads).map(([s,n])=>[s,n.job&&!n.job.ended?{...n,reloaded:!0}:n]));let t=s=>{window.setTimeout(()=>{!this._entryId||!this.isConnected||this._select(this._entryId,!0).then(()=>this._reloading=!1,()=>s>0?t(s-1):this._error=a(this._lang,"reloading"))},2e3)};t(15);return}if(e.available!==void 0&&(this._available=e.available),e.readings){this._readings={...this._readings,...e.readings};let t=new Set((this._faults??[]).flatMap(s=>s.keys));Object.keys(e.readings).some(s=>t.has(s))&&this._loadFaults(1e3)}if(e.programs&&(this._programs={...this._programs,...e.programs}),e.jobs){let t=e.jobs;this._reads=Object.fromEntries(Object.entries(this._reads).map(([s,n])=>[s,n.job&&t[n.job.id]?{...n,job:t[n.job.id]}:n]))}}_scope(e,t){return e?t?`${e}|${t}`:e:Nt}async _readCall(e,t){let s=this._reads[e]??{},n={type:"weishaupt/panel/read_rows",entry_id:this._entryId,start:t};s.device&&(n.device=s.device),s.menu&&(n.menu=s.menu);try{let i=await this.hass.callWS(n);this._reads={...this._reads,[e]:t?{...s,price:void 0,job:i.job}:{...s,price:i}}}catch(i){this._reads={...this._reads,[e]:{...s,error:i.message}}}}_price(e,t){let s=this._scope(e,t);this._reads={...this._reads,[s]:{device:e,menu:t}},this._readCall(s,!1)}async _stopRead(e){let t=this._reads[e];if(t?.job)try{let s=await this.hass.callWS({type:"weishaupt/panel/stop_read",entry_id:this._entryId,job:t.job.id});this._reads={...this._reads,[e]:{...t,job:s}}}catch(s){this._reads={...this._reads,[e]:{...t,error:s.message}}}}_dismissRead(e){let t={...this._reads};delete t[e],this._reads=t}_readBar(e,t){let s=this._lang,n=this._scope(e,t),i=this._reads[n],l=a(s,e?t?"read_scope_menu":"read_scope_device":"read_scope_all");if(!i)return d`<p class="read-bar"><button class="link" @click=${()=>this._price(e,t)}>${l}</button></p>`;let c=d`<button class="link" @click=${()=>this._dismissRead(n)}>${a(s,"dismiss")}</button>`;if(i.error)return d`<p class="read-bar error" role="alert">${i.error} ${c}</p>`;if(i.job){let u=!i.job.ended&&!i.reloaded;return d`<p class="read-bar" role="status">
        ${i.reloaded?a(s,"job_reload"):gt(i.job,s)}
        ${u&&i.job.total?d`<progress max=${i.job.total} value=${i.job.done}></progress>`:p}
        ${u?d`<button class="link" @click=${()=>this._stopRead(n)}>${a(s,"read_stop")}</button>`:c}
      </p>`}return i.price?d`<p class="read-bar">
      <strong>${l}</strong> ${ft(i.price,s)}
      <span class="secondary">${a(s,"read_scope_hint")}</span>
      ${i.price.queued?d`<button class="primary" @click=${()=>this._readCall(n,!0)}>${a(s,"read_start")}</button>`:p}
      ${c}
    </p>`:d`<p class="read-bar secondary">${a(s,"loading")}</p>`}_follows(){return(this._tree?.devices??[]).flatMap(e=>[...e.rows.map(t=>t.follow),...e.programs.map(t=>t.follow)]).filter(e=>!!e)}_followed(e){return this._pending[e.entity_id]??e.enabled}_toggle(e,t){this._pending=re(this._pending,[e],t),this._followNote=void 0}_followCell(e,t=!0,s=""){let n=this._lang;if(!e)return p;if(e.blocked)return d`<span class="secondary">${a(n,"follow_blocked")}</span>`;let i=this._pending[e.entity_id]!==void 0,l=s?`${a(n,"follow")} \u2014 ${s}`:a(n,"follow");return d`<label class=${i?"follow changed":"follow"}>
      <input type="checkbox" aria-label=${l} .checked=${this._followed(e)}
        @change=${c=>this._toggle(e,c.target.checked)} />
      ${t?a(n,"follow"):p}
    </label>`}_followBar(){let e=this._lang,t=Me(this._pending,this._follows()),s=t.enable.length+t.disable.length;return s?d`<div class="message follow-bar" role="status">
      <p>${a(e,"follow_pending",{n:s,enable:t.enable.length,disable:t.disable.length})}</p>
      ${t.enable.length?d`<p class="secondary">${a(e,"follow_reload",{s:30})}</p>`:p}
      ${t.defaultsOff?d`<p class="warning">${a(e,"follow_defaults_off",{n:t.defaultsOff})}</p>`:p}
      <details class="follow-details">
        <summary>${a(e,"follow_details",{n:s})}</summary>
        <ul>
          ${t.enable.map(n=>d`<li><code>+ ${n}</code></li>`)}
          ${t.disable.map(n=>d`<li><code>− ${n}</code></li>`)}
        </ul>
      </details>
      <button class="primary" ?disabled=${this._busy} @click=${()=>this._applyFollow()}>${a(e,"follow_apply")}</button>
      <button class="link" @click=${()=>this._pending={}}>${a(e,"follow_discard")}</button>
    </div>`:this._followNote?d`<div class=${this._followNote.error?"message error":"message"} role="status">
            ${this._followNote.text}
            <button class="ghost" type="button" aria-label=${a(e,"dismiss")} @click=${()=>this._followNote=void 0}>
              ×
            </button>
          </div>`:p}async _applyFollow(){let e=this._lang,t=Me(this._pending,this._follows());this._busy=!0;try{let s=await this.hass.callWS({type:"weishaupt/panel/follow",entry_id:this._entryId,enable:t.enable,disable:t.disable});this._pending={};let n=[a(e,"follow_done",{enabled:s.enabled.length,disabled:s.disabled.length})];s.refused.length&&n.push(a(e,"follow_refused",{n:s.refused.length})),s.reload&&n.push(a(e,"follow_reload_soon",{s:s.reload_after})),this._followNote={text:n.join(" "),error:s.refused.length>0},this._entryId&&await this._select(this._entryId,!0)}catch(s){this._followNote={text:s.message,error:!0}}finally{this._busy=!1}}_open(e){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}_age(e){return ot(Date.now()/1e3-this._offset-e.when,this._lang)}render(){let e=this._lang;return this._error?d`<div class="message error" role="alert">${this._error}</div>`:this._installations===void 0?d`<div class="message">${a(e,"loading")}</div>`:this._installations.length?d`
      <header>
        <h1>${a(e,"title")}</h1>
        ${this._installations.length>1?d`<label
              >${a(e,"installation")}
              <select @change=${t=>this._select(t.target.value)}>
                ${this._installations.map(t=>d`<option value=${t.entry_id} ?selected=${t.entry_id===this._entryId}>${t.title}</option>`)}
              </select></label
            >`:p}
        ${this._clock()}
        ${this._writesPill()}
        ${this._tree?d`<button class="link" @click=${()=>this._report()}>${a(e,"report")}</button>
              <button class="link" @click=${()=>this._csv()}>${a(e,"export_csv")}</button>`:p}
        ${this._rowResult.__report__?d`<span class="error" role="alert">
              ${this._rowResult.__report__.text}
              <button class="ghost" type="button" aria-label=${a(e,"dismiss")} @click=${()=>this._dismissRowResult("__report__")}>×</button>
            </span>`:p}
        ${this._tree?.writes?.clock_writable?d`<button class="link" ?disabled=${this._busy} @click=${()=>this._setClock()}>
              ${a(e,"set_clock")}
            </button>`:p}
        ${this._rowResult.__clock__?d`<span class=${this._rowResult.__clock__.error?"error":"secondary"} role="status">
              ${this._rowResult.__clock__.text}
              <button class="ghost" type="button" aria-label=${a(e,"dismiss")} @click=${()=>this._dismissRowResult("__clock__")}>×</button>
            </span>`:p}
      </header>
      ${this._available?p:d`<div class="message warning" role="status">${a(e,"unavailable")}</div>`}
      ${this._reloading?d`<div class="message" role="status">${a(e,"reloading")}</div>`:p}
      ${this._tree?d`<div class="top-tools">${this._searchBar()}${this._readBar()}</div>`:p}
      ${this._followBar()}
      ${this._tree?this._body(this._tree):d`<div class="message">${a(e,"loading")}</div>`}
      ${this._dialog?this._confirmDialog(this._dialog.answer):p}
    `:d`<div class="message">${a(e,"no_installation")}</div>`}async _call(e){this._busy=!0;try{let t=await this.hass.callWS({...e,entry_id:this._entryId,language:this._lang});return t.guard&&this._tree?.writes&&(this._tree={...this._tree,writes:{...this._tree.writes,...t.guard}}),t}catch(t){let s=t,n=!s?.code||s.code==="connection_lost"||/connection/i.test(s.message??"");return{status:"refused",code:n?"interrupted":s.code,message:n?a(this._lang,"interrupted"):s.message||s.code}}finally{this._busy=!1}}_switchOn(){let e=this._tree?.writes;if(!e)return!1;let t=e.switch_entity_id?this.hass.states[e.switch_entity_id]:void 0;return t?t.state==="on":e.switch}_writesPill(){let e=this._tree?.writes;if(!e)return p;let t=this._lang,s=this._switchOn(),n=e.switch_entity_id?this.hass.states[e.switch_entity_id]:void 0,i=typeof n?.attributes.writes_last_hour=="number"?n.attributes.writes_last_hour:e.writes_last_hour,l=typeof n?.attributes.max_writes_per_hour=="number"?n.attributes.max_writes_per_hour:e.max_per_hour,c=s?a(t,"writes_pill_on",{n:i,max:l}):a(t,"writes_pill_off");return e.switch_entity_id?d`<button class="writes-pill ${s?"on":"off"}" @click=${()=>this._open(e.switch_entity_id)}>
        ${c}
      </button>`:d`<span class="writes-pill ${s?"on":"off"}">${c}</span>`}_switchOffHint(){let e=this._lang,t=this._tree?.writes?.switch_entity_id;return d`<div class="error">
      ${a(e,"switch_off_hint")}
      ${t?d` <button class="link" type="button" @click=${()=>this._open(t)}>${a(e,"open_switch")}</button>`:p}
    </div>`}_resultText(e){let t=this._lang;return e.status==="refused"?{text:a(t,"not_written",{message:e.message??""}),error:!0}:e.kind==="clock"||e.requested!==void 0?{text:a(t,"clock_sent",{requested:e.requested??"",frame:e.frame??"",result:e.result_text??e.result??""}),error:e.result!=="sent"}:{text:a(t,"written_line",{before:e.before??"-",after:e.after??"",frame:e.frame?` (${e.frame})`:"",result:e.result_text??e.result??""}),error:e.result!=="ok"&&e.result!=="unchanged"}}_writing(e){this._rowResult={...this._rowResult,[e]:{text:a(this._lang,"writing"),error:!1}}}async _writeRow(e){let t=e.writable,s=Number(this._draft);this._writing(e.key);let n=await this._call({type:"weishaupt/panel/write",key:t.key,value:s});this._handle(n,e.key),n.status!=="refused"&&(this._editing=void 0)}_handle(e,t){if(e.status==="confirm"){this._dialog={answer:e,target:t};return}this._rowResult={...this._rowResult,[t]:this._resultText(e)}}async _setClock(){this._writing("__clock__"),this._handle(await this._call({type:"weishaupt/panel/clock"}),"__clock__")}async _confirmed(){let e=this._dialog;this._dialog=void 0,this._writing(e.target);let t=await this._call({type:"weishaupt/panel/confirm",pending_id:e.answer.pending_id});this._rowResult={...this._rowResult,[e.target]:this._resultText(t)}}async _withdrawn(){let e=this._dialog;this._dialog=void 0;let t={...this._rowResult};delete t[e.target],this._rowResult=t,await this._call({type:"weishaupt/panel/cancel",pending_id:e.answer.pending_id})}_dialogKeydown(e){if(e.key==="Escape"){this._withdrawn();return}if(e.key!=="Tab")return;let t=e.currentTarget,s=Array.from(t.querySelectorAll("button:not([disabled]), [href], input, select, [tabindex]:not([tabindex='-1'])"));if(!s.length)return;let n=s[0],i=s[s.length-1],l=this.renderRoot instanceof ShadowRoot?this.renderRoot.activeElement:document.activeElement;e.shiftKey&&l===n?(e.preventDefault(),i.focus()):!e.shiftKey&&l===i&&(e.preventDefault(),n.focus())}_confirmDialog(e){let t=this._lang,s=e.placeholders??{},n=e.kind==="clock";return d`<div
      class="backdrop"
      @click=${i=>i.target===i.currentTarget&&void this._withdrawn()}
    >
      <div
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        @keydown=${i=>this._dialogKeydown(i)}
      >
        <h2 id="confirm-title">${a(t,"confirm_title",{setting:s.setting??"",device:s.device??""})}</h2>
        ${n?d`<p>${a(t,"clock_current",{current:s.current??"-"})}</p>
              <p>${a(t,"clock_confirm",{send_at:s.send_at??"",late:s.late??""})}</p>`:d`<dl>
                <dt>${a(t,"current")}</dt>
                <dd>${s.current}</dd>
                <dt>${a(t,"new_value")}</dt>
                <dd><strong>${s.requested}</strong></dd>
                <dt>${a(t,"allowed")}</dt>
                <dd>${s.allowed}</dd>
              </dl>
              <p>${a(t,"path",s)}</p>
              <p class="secondary">${a(t,"regulation_note")}</p>`}
        <div class="actions">
          <button class="link cancel" @click=${()=>this._withdrawn()}>${a(t,"cancel")}</button>
          <button class="primary" @click=${()=>this._confirmed()}>
            ${a(t,n?"confirm_clock":"confirm")}
          </button>
        </div>
      </div>
    </div>`}_dismissRowResult(e){let t={...this._rowResult};delete t[e],this._rowResult=t}_dismissWeekResult(e){let t={...this._weekResult};delete t[e],this._weekResult=t}_writeCell(e){let t=this._lang,s=e.writable;if(e.edited_on)return d`<span class="secondary">${a(t,"edited_on_setting",{device:f(e.edited_on.device,t)})}</span>`;if(!s)return d`<span class="secondary">${a(t,"read_only")}</span>`;let n=this._rowResult[e.key],i=d`<span class="badge ${s.risk}">${a(t,s.risk)}</span>${s.through?d`<div class="secondary">${a(t,"through",{circuit:s.through})}</div>`:p}`,l=p;return s.offered?this._editing===e.key?l=p:l=d`<button class="link" @click=${()=>this._startEdit(e)}>${a(t,"edit")}</button>`:l=d`<div class="secondary">
        ${s.why_not==="writes_disabled"?a(t,"not_offered_writes_disabled"):a(t,"not_offered",{reason:s.why_not??""})}
      </div>`,d`${i}${l}${n?d`<div class=${n.error?"error":"secondary"} role="status">
          ${n.text}
          <button class="ghost" type="button" aria-label=${a(t,"dismiss")} @click=${()=>this._dismissRowResult(e.key)}>×</button>
        </div>`:p}`}_editForm(e){let t=this._lang,s=e.writable,n=O(e,this._readings),i=Ee(e,n),l=i!==""&&this._draft===i,c=this._switchOn(),u=Ae(e,t);return d`<form
        class="edit"
        @keydown=${h=>h.key==="Escape"&&(this._editing=void 0)}
        @submit=${h=>{h.preventDefault(),this._writeRow(e)}}
      >
        ${s.options?d`<select aria-label=${a(t,"new_value")}
              @change=${h=>this._draft=h.target.value}>
              <option value="" ?selected=${this._draft===""} disabled>…</option>
              ${s.options.map(h=>d`<option value=${h.raw} ?selected=${String(h.raw)===this._draft}>${f(h.label,t)}</option>`)}
            </select>`:d`<input type="number" aria-label=${a(t,"new_value")} .value=${this._draft}
              min=${s.minimum??""} max=${s.maximum??""} step=${s.step??"any"}
              @input=${h=>this._draft=h.target.value} />${e.unit?d` ${e.unit}`:p}${u?d` <span class="secondary">(${u})</span>`:p}`}
        <button class="primary" type="submit" ?disabled=${this._busy||this._draft===""||l||!c}>
          ${a(t,"write_now")}
        </button>
        <button class="link" type="button" @click=${()=>this._editing=void 0}>${a(t,"cancel")}</button>
        <div class="secondary">
          ${Re(e,n,t)??"-"} ·
          ${a(t,"path_short",{address:s.address??"",register:s.register??"",source:s.source})}
        </div>
        <div class="secondary">${a(t,s.risk==="comfort"?"comfort_note":"regulation_note")}</div>
        ${this._tree?.writes&&!c?this._switchOffHint():p}
      </form>`}_startEdit(e){this._draft=Ee(e,O(e,this._readings)),this._editing=e.key}_dayText(e,t){let s=e?.[t];return s==null?null:K(s.map(([n,i])=>[vt(n),vt(i)]))}_startWeek(e){let t=this._programs[e.key],s={};for(let n=1;n<=7;n++)s[String(n)]=this._dayText(t,String(n))??"";this._weekDraft={...this._weekDraft,[e.key]:s},this._weekResult={...this._weekResult,[e.key]:void 0}}_setDay(e,t,s){this._weekDraft={...this._weekDraft,[e]:{...this._weekDraft[e],[t]:s}};let n=`${e}|${t}`;if(this._dragError[n]){let i={...this._dragError};delete i[n],this._dragError=i}}_changed(e){let t=this._weekDraft[e.key]??{},s=this._programs[e.key];return Object.keys(t).filter(n=>{let i=this._dayText(s,n);if(i===null&&t[n].trim()==="")return!1;let l=N(t[n]);return("ranges"in l?K(l.ranges):t[n])!==i})}async _writeWeek(e){let t=this._weekDraft[e.key],s={};for(let h of this._changed(e))s[h]=t[h];this._weekResult={...this._weekResult,[e.key]:{text:a(this._lang,"writing"),error:!1}};let n=await this._call({type:"weishaupt/panel/write_days",program:e.key,days:s}),i=this._lang;if(n.status==="refused"){this._weekResult={...this._weekResult,[e.key]:this._resultText(n)};return}let l=T[i]??T.en,c=Object.entries(n.days??{}).map(([h,_])=>a(i,"written_line",{before:`${l[Number(h)-1]} ${_.before??"-"}`,after:_.after??"",frame:_.frames?.length?` (${_.frames.join(", ")})`:"",result:_.result_text??_.result??""}));this._weekResult={...this._weekResult,[e.key]:{text:c.join(" \xB7 "),error:!1}};let u={...this._weekDraft};delete u[e.key],this._weekDraft=u}_copy(e,t,s){let n=this._weekDraft[e][t],i=s==="all"?["1","2","3","4","5","6","7"]:s==="weekdays"?["1","2","3","4","5"]:s==="weekend"?["6","7"]:[s],l={...this._weekDraft[e]};for(let c of i)c!==t&&(l[c]=n);this._weekDraft={...this._weekDraft,[e]:l}}_dragStart(e,t,s){let n=e.currentTarget;if(e.target.classList.contains("bar"))return;let i=n.getBoundingClientRect(),l=(e.clientX-i.left)/i.width;this._drag={program:t,day:s,from:l,element:n};let[c,u]=se(l,l);this._dragPreview={program:t,day:s,start:c,end:u},n.setPointerCapture(e.pointerId)}_dragMove(e){let t=this._drag;if(!t)return;let s=t.element.getBoundingClientRect(),[n,i]=se(t.from,(e.clientX-s.left)/s.width);this._dragPreview={program:t.program,day:t.day,start:n,end:i}}_dragCancel(){this._drag=void 0,this._dragPreview=void 0}_dragEnd(e){let t=this._drag;if(this._drag=void 0,this._dragPreview=void 0,!t)return;let s=t.element.getBoundingClientRect(),n=N(this._weekDraft[t.program][t.day]);if(!("ranges"in n))return;let i=dt(n.ranges,t.from,(e.clientX-s.left)/s.width);i?this._setDay(t.program,t.day,K(i)):this._dragError={...this._dragError,[`${t.program}|${t.day}`]:"day_too_many"}}_removeRange(e,t,s){let n=N(this._weekDraft[e][t]);"ranges"in n&&this._setDay(e,t,K(n.ranges.filter((i,l)=>l!==s)))}_clock(){let e=this._tree?.clock.entity_id,t=e?this.hass.states[e]:void 0;if(!e||!t||Number.isNaN(Number(t.state)))return p;let s=this._lang,n=Math.round(Number(t.state)),i=n===0?a(s,"clock_on_time"):a(s,n>0?"clock_ahead":"clock_behind",{n:Math.abs(n)});return d`<button class="clock link" @click=${()=>this._open(e)}>
      ${a(s,"clock_line",{label:a(s,"clock_offset"),text:i})}
    </button>`}_searchActive(){return this._query.trim()!==""||this._filter!=="all"}_clearSearch(){this._query="",this._filter="all"}_searchBar(){let e=this._lang,t=[["all",a(e,"filter_all")],["writable",a(e,"filter_writable")],["followed",a(e,"filter_followed")],["unread",a(e,"filter_unread")]];return d`<div class="search-bar" role="search">
      <input
        type="search"
        .value=${this._query}
        placeholder=${a(e,"search_placeholder")}
        aria-label=${a(e,"search_placeholder")}
        @input=${s=>this._query=s.target.value}
        @keydown=${s=>s.key==="Escape"&&this._clearSearch()}
      />
      <div class="filters" role="group">
        ${t.map(([s,n])=>d`<button
            type="button"
            class="filter-pill ${this._filter===s?"active":""}"
            aria-pressed=${this._filter===s?"true":"false"}
            @click=${()=>this._filter=s}
          >
            ${n}
          </button>`)}
      </div>
      ${this._searchActive()?d`<button type="button" class="link" @click=${()=>this._clearSearch()}>${a(e,"search_clear")}</button>`:p}
    </div>`}_searchView(e){let t=this._lang,s=e.devices.map(i=>({device:i,rows:i.rows.filter(l=>yt(l,this._query,this._filter,this._readings,t))})).filter(i=>i.rows.length>0),n=s.reduce((i,l)=>i+l.rows.length,0);return d`<h2>${a(t,n===1?"search_results_one":"search_results",{n})}</h2>
      ${n===0?d`<p class="secondary">${a(t,"search_empty")}</p>`:s.map(({device:i,rows:l})=>d`<h3>${f(i.label,t)} (${l.length})</h3>
              ${this._table(l)}`)}`}_body(e){let t=e.devices.find(s=>s.id===this._device);return d`<div class=${this.narrow?"layout narrow":"layout"}>
      <nav aria-label=${a(this._lang,"devices")}>${this._nav(e)}</nav>
      <main>
        ${this._searchActive()?this._searchView(e):this._menu===ne?this._definitions(e):this._menu===ie?(()=>{let s=this._faults?.find(n=>n.device===this._device);return s?this._faultsView(s):d`<p class="secondary">${a(this._lang,"loading")}</p>`})():t?this._device_view(t):p}
      </main>
    </div>`}_faultBadge(e){let t=this._faults?.find(n=>n.device===e);if(!t)return 0;let s=t.history?.entries?.length??0;return s>0?s:(t.counters??[]).filter(n=>(n.count??0)>0).length}_menuPendingCount(e,t){let s=e.rows.filter(i=>(i.menu===t||wt(e.menus,i.menu,t))&&i.follow&&this._pending[i.follow.entity_id]!==void 0).length,n=t===je?e.programs.filter(i=>i.follow&&this._pending[i.follow.entity_id]!==void 0).length:0;return s+n}_nav(e){let t=this._lang,s=(i,l)=>{this._device=i,this._menu=l,this._searchActive()&&this._clearSearch()};if(this.narrow){let i=`${this._device??""}|${this._menu??""}`;return d`<label class="choose"
        >${a(t,"devices")}
        <select
          @change=${l=>{let[c,u]=l.target.value.split("|");s(c,u)}}
        >
          ${e.devices.map(l=>d`<optgroup label=${f(l.label,t)}>
              ${J(l.menus).map(([c,u])=>d`<option value=${`${l.id}|${c.id}`} ?selected=${i===`${l.id}|${c.id}`}>
                    ${"\xA0\xA0".repeat(u)}${f(c.label,t)}
                  </option>`)}
              ${this._faults?.some(c=>c.device===l.id)?d`<option value=${`${l.id}|${ie}`} ?selected=${i===`${l.id}|${ie}`}>
                    ${a(t,"faults")}
                  </option>`:p}
            </optgroup>`)}
          <option value=${`${this._device??""}|${ne}`} ?selected=${this._menu===ne}>
            ${a(t,"definitions")}
          </option>
        </select></label
      >`}let n=(i,l,c,u,h="")=>{let _=!this._searchActive()&&this._device===i&&this._menu===l;return d`<li>
        <button
          class="menu depth${u}"
          aria-current=${_?"page":"false"}
          @click=${()=>s(i,l)}
        >
          <span>${c}</span>
          ${h?d`<span class="nav-badge">${h}</span>`:p}
        </button>
      </li>`};return d`<ul>
      ${e.devices.map(i=>{let l=this._faultBadge(i.id),c=i.programs.some(u=>this._weekDraft[u.key]!==void 0);return d`<li>
          <span class="device">${f(i.label,t)}</span>
          <ul>
            ${J(i.menus).map(([u,h])=>{let _=this._menuPendingCount(i,u.id),g=u.id===je&&c?"\u2022":_>0?String(_):"";return n(i.id,u.id,f(u.label,t),h,g)})}
            ${this._faults?.some(u=>u.device===i.id)?n(i.id,ie,a(t,"faults"),0,l>0?String(l):""):p}
          </ul>
        </li>`})}
      <li class="nav-sep" role="separator"></li>
      ${n(this._device??"",ne,a(t,"definitions"),0)}
    </ul>`}_device_view(e){let t=this._lang,s=e.menus.find(l=>l.id===this._menu),n=[e.addresses.length?`${a(t,"address")} ${e.addresses.join(", ")}`:"",e.software?`${a(t,"software")} ${e.software}`:"",e.hardware?`${a(t,"hardware")} ${e.hardware}`:""].filter(Boolean),i=J(e.menus).filter(([l])=>l.id===this._menu||wt(e.menus,l.id,this._menu??"")).map(([l])=>[l,e.rows.filter(c=>c.menu===l.id)]).filter(([,l])=>l.length);return d`<h2>${f(e.label,t)}${s?d` — ${f(s.label,t)}`:p}</h2>
      ${n.length?d`<p class="secondary">${n.join(" \xB7 ")}</p>`:p}
      ${e.rows.some(l=>!l.listened&&l.read&&!l.passive)?this._readBar(e.id):p}
      ${this._menu===je?this._programs_view(e):p}
      ${i.length?d`<p class="secondary">${a(t,"write_hint")}</p>`:p}
      ${i.map(([l,c])=>d`${l.id!==this._menu?d`<h3>${f(l.label,t)}</h3>`:p}
          <div class="table-tools">
            ${c.some(u=>!u.listened&&u.read&&!u.passive)?this._readBar(e.id,l.id):p}
            ${c.some(u=>u.follow&&!u.follow.blocked)?d`<span>
                  <button class="ghost" @click=${()=>this._pending=re(this._pending,c.map(u=>u.follow),!0)}>
                    ${a(t,"follow_all")}</button>
                  <button class="ghost" @click=${()=>this._pending=re(this._pending,c.map(u=>u.follow),!1)}>
                    ${a(t,"follow_none")}</button>
                </span>`:p}
          </div>
          ${this._table(c)}`)}`}_codeHeader(){let e=this._lang,t={"":"asc",asc:"desc",desc:""},s=this._codeSort;return d`<th scope="col" aria-sort=${s==="asc"?"ascending":s==="desc"?"descending":"none"}>
      <button type="button" class="sort" title=${a(e,"sort_by_code")} @click=${()=>this._codeSort=t[s]}>
        ${a(e,"code")}<span aria-hidden="true">${s==="asc"?" \u25B2":s==="desc"?" \u25BC":" \u2195"}</span>
      </button>
    </th>`}_codeCell(e){let t=Pe(e);if(!t)return d`<td></td>`;let s=mt(e,this._lang);return d`<td class="nowrap code"><abbr title=${s} aria-label=${`${t} (${s})`}>${t}</abbr></td>`}_table(e){let t=this._lang;return this._tick,e=bt(e,this._codeSort),d`<div class="scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">${a(t,"name")}</th>
              ${this._codeHeader()}
              <th scope="col">${a(t,"value")}</th>
              <th scope="col">${a(t,"age")}</th>
              <th scope="col">${a(t,"range")}</th>
              <th scope="col">${a(t,"write")}</th>
              <th scope="col">${a(t,"entity")}</th>
              <th scope="col">${a(t,"follow")}</th>
            </tr>
          </thead>
          <tbody>
            ${e.map(s=>{let n=O(s,this._readings),i=Re(s,n,t),l=nt(f(s.description,t),f(s.label,t))?"":f(s.description,t);return d`<tr>
                <th scope="row">
                  ${f(s.label,t)}
                  ${l?d`<div class="description">${l}</div>`:p}
                </th>
                ${this._codeCell(s)}
                <td class="nowrap num">${i??d`<span class="secondary">${a(t,Se(s))}</span>`}</td>
                <td class="secondary nowrap">
                  ${n?this._age(n):""}${n?.kept?d`<div class="kept">${a(t,"kept")}</div>`:p}${s.passive?d`<div>${a(t,"passive")}</div>`:p}${n?.once&&!s.passive?d`<div class="kept">${a(t,"read_once")}</div>`:p}
                </td>
                <td class="nowrap num">${Ae(s,t)}</td>
                <td>${this._writeCell(s)}</td>
                <td>
                  ${s.entity_id?d`<button class="ghost" @click=${()=>this._open(s.entity_id)}>${a(t,"open")}</button>`:p}
                </td>
                <td class="follow-cell">${this._followCell(s.follow,!1,f(s.label,t))}</td>
              </tr>${this._editing===s.key?d`<tr class="edit-row"><td colspan="8">${this._editForm(s)}</td></tr>`:p}`})}
          </tbody>
        </table>
      </div>`}_programs_view(e){let t=this._lang,s=T[t]??T.en,n=this._tree?.writes;return d`${e.programs.map(i=>{let l=this._programs[i.key],c=this._weekDraft[i.key],u=c!==void 0,h=u?this._changed(i):[],_=u?Object.fromEntries(Object.entries(c).map(([w,$])=>{let m=N($);return[w,"error"in m?m.error:null]})):{},g=Object.values(_).some(Boolean),y=i.edited_on?a(t,"edited_on_program",{program:f(i.edited_on.label,t),device:f(i.edited_on.device,t)}):i.read?i.listened?i.writable?a(t,"editable"):a(t,"not_editable"):a(t,"program_not_listened"):a(t,"not_read_program"),v=this._weekResult[i.key];return d`<section class="program">
        <h3>
          ${f(i.label,t)}
          ${i.stored_only?d`<span class="badge">${a(t,"stored_only_badge")}</span>`:p}
          ${i.entity_id?d`<button class="link" @click=${()=>this._open(i.entity_id)}>${a(t,"open")}</button>`:p}
          ${i.writable&&n&&!u?d`<button class="link" @click=${()=>this._startWeek(i)}>${a(t,"edit_days")}</button>`:p}
          ${this._followCell(i.follow)}
        </h3>
        <p class="secondary">${y}</p>
        ${i.stored_only?d`<p class="secondary">${a(t,"stored_only_note")}</p>`:p}
        ${i.read&&!i.listened?this._queued[i.key]!==void 0?d`<p class="secondary" role="status">${Ce(this._queued[i.key],t)}</p>`:d`<p>
                <button class="link" @click=${()=>this._readProgram(i.key)}>${a(t,"read_now")}</button>
                <span class="secondary"
                  >${a(t,"read_cost",{n:i.to_read,s:Math.round(i.to_read*2.2)})}</span
                >
              </p>`:p}
        ${u?d`<p class="secondary">${a(t,"drag_hint")}</p>`:p}
        ${u?d`<table class="week">
          <caption class="visually-hidden">${f(i.label,t)}</caption>
          <thead>
            <tr>
              <th scope="col"><span class="visually-hidden">${a(t,"programs")}</span></th>
              <td class="scale" aria-hidden="true">
                ${[0,6,12,18,24].map(w=>d`<span style="left:${w/24*100}%">${w}</span>`)}
              </td>
            </tr>
          </thead>
          <tbody>
            ${s.map((w,$)=>{let m=String($+1);if(u){let qe=N(c[m]),$t="ranges"in qe?qe.ranges:[],oe=_[m]??this._dragError[`${i.key}|${m}`]??null,E=this._dragPreview?.program===i.key&&this._dragPreview.day===m?this._dragPreview:void 0;return d`<tr class=${h.includes(m)?"changed":""}>
                  <th scope="row">${w}</th>
                  <td>
                    <div
                      class="day editable"
                      aria-hidden="true"
                      @pointerdown=${b=>this._dragStart(b,i.key,m)}
                      @pointermove=${b=>this._dragMove(b)}
                      @pointerup=${b=>this._dragEnd(b)}
                      @pointercancel=${()=>this._dragCancel()}
                    >
                      ${$t.map(([b,k],xt)=>d`<span
                          class="bar"
                          title=${a(t,"bar_remove_hint",{range:`${q(b)}-${q(k)}`})}
                          style="left:${b/1440*100}%;width:${(k-b)/1440*100}%"
                          @click=${()=>this._removeRange(i.key,m,xt)}
                        ></span>`)}
                      ${E?d`<span
                              class="bar preview"
                              style="left:${E.start/1440*100}%;width:${(E.end-E.start)/1440*100}%"
                            ></span>
                            <span
                              class="drag-label"
                              style="left:${(E.start+E.end)/2880*100}%"
                            >${q(E.start)}–${q(E.end)}</span>`:p}
                    </div>
                    <div class="day-edit">
                      <input
                        type="text"
                        aria-label=${w}
                        aria-invalid=${oe?"true":"false"}
                        placeholder=${l?.[m]==null?a(t,"day_unread"):""}
                        .value=${c[m]}
                        @input=${b=>this._setDay(i.key,m,b.target.value)}
                      />
                      <button
                        class="ghost"
                        type="button"
                        ?disabled=${c[m].trim()===""||c[m].trim()==="-"}
                        @click=${()=>this._setDay(i.key,m,"-")}
                      >
                        ${a(t,"clear_day")}
                      </button>
                      <label class="secondary"
                        >${a(t,"copy_to")}
                        <select
                          @change=${b=>{let k=b.target;k.value&&this._copy(i.key,m,k.value),k.value=""}}
                        >
                          <option value="">…</option>
                          <option value="all">${a(t,"copy_all")}</option>
                          <option value="weekdays">${a(t,"copy_weekdays")}</option>
                          <option value="weekend">${a(t,"copy_weekend")}</option>
                          ${s.map((b,k)=>k===$?p:d`<option value=${String(k+1)}>${b}</option>`)}
                        </select></label
                      >
                    </div>
                    ${oe?d`<div class="error" role="alert">${a(t,oe)}</div>`:p}
                  </td>
                </tr>`}return p})}
          </tbody>
        </table>`:d`<weishaupt-week-grid
              .days=${l}
              language=${t}
              unread=${a(t,i.listened?"day_unread":"not_listened")}
              caption=${f(i.label,t)}
              today=${_t(new Date)}
            ></weishaupt-week-grid>`}
        ${u&&n?d`<p class="secondary">
                ${a(t,h.length===1?"cost_one":"cost",{days:h.length,writes:h.length*3,used:n.writes_last_hour,max:n.max_per_hour})}
              </p>
              ${this._switchOn()?p:this._switchOffHint()}
              <div class="actions">
                <button class="link" @click=${()=>{let w={...this._weekDraft};delete w[i.key],this._weekDraft=w}}>${a(t,"discard")}</button>
                <button class="primary" ?disabled=${this._busy||g||!h.length||!this._switchOn()}
                  @click=${()=>this._writeWeek(i)}>${a(t,"write_days")}</button>
              </div>`:p}
        ${v?d`<p class=${v.error?"error":"secondary"} role="status">
              ${v.text}
              <button class="ghost" type="button" aria-label=${a(t,"dismiss")} @click=${()=>this._dismissWeekResult(i.key)}>×</button>
            </p>`:p}
      </section>`})}`}_definitions(e){let t=this._lang,s=e.definitions,n=l=>{if(!l.length)return d`${a(t,"none")}`;let c=d`<ul>${l.map(h=>d`<li><code>${h}</code></li>`)}</ul>`;if(l.length<=5)return c;let u=a(t,l.length===1?"items_count_one":"items_count",{n:l.length});return d`<details><summary>${u}</summary>${c}</details>`},i=e.writes;return d`<h2>${a(t,"definitions")}</h2>
      <dl>
        <dt>${a(t,"in_use")}</dt>
        <dd>
          ${s.version}${s.commit?d` <code>${s.commit.slice(0,7)}</code>`:p} —
          ${s.source==="bundled"?a(t,"source_bundled"):a(t,"source_file",{file:s.source})}
        </dd>
        <dt>${a(t,"ebusd")}</dt>
        <dd>
          ${e.ebusd.endpoint??"?"} · ${e.ebusd.version??"?"}${e.ebusd.own_address?` (${e.ebusd.own_address})`:""} ·
          ${a(t,"capability",{value:e.ebusd.capability})} ·
          ${a(t,e.ebusd.mode==="follow"?"mode_follow":"mode_pinned",{n:e.ebusd.endpoints.length})}
        </dd>
        <dt>${a(t,"writes")}</dt>
        <dd>
          ${i?d`${a(t,this._switchOn()?"switch_on":"switch_off")} ·
              ${a(t,"capability",{value:i.capability})} ·
              ${a(t,"per_hour",{n:i.writes_last_hour,max:i.max_per_hour})}`:a(t,"writes_off")}
        </dd>
        <dt>${a(t,"messages")}</dt>
        <dd>
          ${a(t,"readable",{usable:s.usable,readable:s.usable+s.not_usable.filter(l=>l.reason==="mismatch"||l.reason==="other").length})}
        </dd>
        <dt>${a(t,"not_usable")}</dt>
        <dd>${n(it(s.not_usable,t))}</dd>
        <dt>${a(t,"refused")}</dt>
        <dd>${n(Object.entries(s.refused).map(([l,c])=>`${l}: ${c}`))}</dd>
        <dt>${a(t,"mismatches")}</dt>
        <dd>${n(s.mismatches.map(l=>`${l.key}: ${l.reason}${l.detail?` (${l.detail})`:""}`))}</dd>
        <dt>${a(t,"unknown_addresses")}</dt>
        <dd>${n(e.unknown_addresses)}</dd>
        <dt>${a(t,"named_from_metadata")}</dt>
        <dd>
          ${n(s.named_from_metadata.map(l=>l.disabled?`${l.entity_id} (${a(t,"disabled")})`:l.entity_id))}
        </dd>
        <dt>${a(t,"not_named")}</dt>
        <dd>${n(s.not_named)}</dd>
        ${i?d`<dt>${a(t,"read_only_settings")}</dt>
              <dd>${n(i.read_only.map(l=>`${l.key}: ${l.reason}`))}</dd>`:p}
      </dl>`}};Z.properties={hass:{attribute:!1},narrow:{type:Boolean},_installations:{state:!0},_entryId:{state:!0},_tree:{state:!0},_readings:{state:!0},_programs:{state:!0},_available:{state:!0},_device:{state:!0},_menu:{state:!0},_error:{state:!0},_tick:{state:!0},_queued:{state:!0},_reloading:{state:!0},_editing:{state:!0},_draft:{state:!0},_rowResult:{state:!0},_busy:{state:!0},_dialog:{state:!0},_weekDraft:{state:!0},_weekResult:{state:!0},_faults:{state:!0},_reads:{state:!0},_pending:{state:!0},_followNote:{state:!0},_hideZeroFaults:{state:!0},_query:{state:!0},_filter:{state:!0},_codeSort:{state:!0},_dragPreview:{state:!0},_dragError:{state:!0}},Z.styles=F`
    .read-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin: 4px 0;
    }
    .top-tools {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px 16px;
      padding: 8px 16px 0;
    }
    .search-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 8px;
      flex: 1 1 320px;
    }
    .search-bar input[type="search"] {
      flex: 1 1 200px;
      max-width: 340px;
      min-width: 0;
    }
    .filters {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .filter-pill {
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--secondary-text-color);
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.85em;
      cursor: pointer;
    }
    .filter-pill.active {
      border-color: var(--primary-color);
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    .read-bar progress {
      width: 160px;
    }
    .table-tools {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    .follow {
      white-space: nowrap;
      font-weight: normal;
      font-size: 0.9em;
    }
    .follow.changed {
      font-style: italic;
    }
    .follow-bar {
      position: sticky;
      top: 0;
      z-index: 2;
      background: var(--card-background-color, var(--primary-background-color));
      border-bottom: 1px solid var(--divider-color);
      border-inline-start: 4px solid var(--primary-color);
    }
    .follow-bar p {
      margin: 0 0 6px;
    }
    .follow-details {
      margin: 0 0 8px;
      font-size: 0.9em;
    }
    .follow-details ul {
      margin: 4px 0 0;
      padding-inline-start: 18px;
      max-height: 160px;
      overflow-y: auto;
    }
    .writes-pill {
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.9em;
      border: 1px solid currentColor;
      background: none;
      cursor: pointer;
    }
    .writes-pill.on {
      color: var(--success-color, var(--primary-color));
    }
    .writes-pill.off {
      color: var(--secondary-text-color);
    }
    .nav-sep {
      border-top: 1px solid var(--divider-color);
      margin: 10px 0;
    }
    .num {
      font-variant-numeric: tabular-nums;
    }
    td.code abbr {
      text-decoration: underline dotted;
      cursor: help;
    }
    th button.sort {
      background: none;
      border: none;
      padding: 0;
      font: inherit;
      color: inherit;
      cursor: pointer;
      white-space: nowrap;
    }
    th button.sort:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .follow-cell {
      text-align: center;
    }
    .inline-check {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin: 0 0 8px;
      cursor: pointer;
    }
    details summary {
      cursor: pointer;
      color: var(--primary-color);
    }
    details[open] summary {
      margin-bottom: 4px;
    }
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
      padding: 12px 16px;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      font-size: 20px;
      font-weight: 400;
      margin: 0;
    }
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 4px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(200px, 260px) 1fr;
      gap: 16px;
      padding: 16px;
    }
    .layout.narrow {
      grid-template-columns: 1fr;
    }
    nav,
    main {
      background: var(--card-background-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color);
      padding: 12px;
      min-width: 0;
    }
    nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    label.choose {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    select {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    .device {
      display: block;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    button {
      font: inherit;
      color: inherit;
    }
    button.menu {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    .nav-badge {
      font-size: 0.78em;
      padding: 0 6px;
      border-radius: 10px;
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button.menu.depth1 {
      padding-inline-start: 24px;
    }
    button.menu.depth2 {
      padding-inline-start: 40px;
    }
    button.menu[aria-current="page"] {
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 8px;
      cursor: pointer;
      color: var(--primary-color);
    }
    button.ghost {
      border: 0;
      background: none;
      border-radius: 6px;
      padding: 2px 6px;
      cursor: pointer;
      color: var(--primary-color);
    }
    button.ghost:hover:not(:disabled) {
      background: var(--secondary-background-color);
    }
    .nowrap {
      white-space: nowrap;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    thead th {
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    tbody th {
      font-weight: 400;
      min-width: 12em;
    }
    tbody tr:hover {
      background: var(--secondary-background-color);
    }
    tr.edit-row,
    tr.edit-row:hover {
      background: var(--secondary-background-color);
    }
    .description,
    .secondary {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .kept {
      font-style: italic;
    }
    .badge {
      white-space: nowrap;
      border-radius: 10px;
      padding: 1px 8px;
      border: 1px solid currentColor;
    }
    .badge.comfort {
      color: var(--success-color, var(--primary-color));
    }
    .badge.regulation {
      color: var(--warning-color, var(--primary-color));
    }
    .message {
      padding: 16px;
    }
    .message.error {
      color: var(--error-color);
    }
    .message.warning,
    .follow-bar .warning {
      color: var(--warning-color);
    }
    table.week th {
      width: 8em;
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .scale span:first-child {
      transform: none;
    }
    .scale span:last-child {
      transform: translateX(-100%);
    }
    .day {
      position: relative;
      height: 14px;
      background-color: var(--secondary-background-color);
      background-image: linear-gradient(
        to right,
        transparent calc(25% - 0.5px),
        var(--divider-color) 25%,
        transparent calc(25% + 0.5px),
        transparent calc(50% - 0.5px),
        var(--divider-color) 50%,
        transparent calc(50% + 0.5px),
        transparent calc(75% - 0.5px),
        var(--divider-color) 75%,
        transparent calc(75% + 0.5px)
      );
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    dl {
      display: grid;
      grid-template-columns: minmax(0, max-content) minmax(0, 1fr);
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
      min-width: 0; /* a long entity id wraps inside its column instead of widening the page */
      overflow-wrap: anywhere;
    }
    code {
      overflow-wrap: anywhere;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .error {
      color: var(--error-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      cursor: pointer;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    form.edit {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px 8px;
      margin-top: 6px;
    }
    form.edit div {
      flex-basis: 100%;
    }
    input {
      font: inherit;
      padding: 4px 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[type="number"] {
      width: 6em;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .day.editable {
      cursor: crosshair;
      height: 22px;
      touch-action: none;
    }
    .day.editable .bar {
      cursor: pointer;
    }
    .day.editable .bar:hover {
      background: var(--error-color);
    }
    .bar.preview {
      opacity: 0.45;
      pointer-events: none;
    }
    .drag-label {
      position: absolute;
      top: -22px;
      transform: translateX(-50%);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.78em;
      white-space: nowrap;
      background: var(--primary-text-color);
      color: var(--card-background-color);
      pointer-events: none;
      z-index: 3;
    }
    .day-edit {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 12px;
      margin-top: 4px;
      align-items: center;
    }
    .day-edit input {
      flex: 1 1 14em;
      min-width: 0;
    }
    tr.changed th {
      font-weight: 500;
      color: var(--primary-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px 20px;
      max-width: 560px;
      width: 100%;
      max-height: 90vh;
      overflow: auto;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    @media (max-width: 600px) {
      dl {
        grid-template-columns: 1fr;
      }
    }
  `;customElements.get("weishaupt-panel")||customElements.define("weishaupt-panel",Z);function vt(o){let[r,e]=o.split(":").map(Number);return r*60+(e||0)}export{Z as WeishauptPanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
